import math
from typing import Any
import numpy as np
import pybullet as pb
import pybullet_data
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


SHAPE_MAP = {
    "sphere": pb.GEOM_SPHERE,
    "box": pb.GEOM_BOX,
    "cylinder": pb.GEOM_CYLINDER,
}


class PyBulletTool(SimulationTool):
    name = "PyBullet"
    key = "pybullet"
    layer = "mechanics"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "collision")
        if sim_type not in ("free_fall", "collision", "pendulum", "projectile", "custom_urdf"):
            raise ValueError(f"Unknown simulation_type: {sim_type}")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("gravity", -9.81)
        params.setdefault("timestep", 1.0 / 240.0)
        params.setdefault("duration", 5.0)
        params.setdefault("restitution", 0.9)
        params.setdefault("friction", 0.5)

        if sim_type in ("free_fall", "collision", "projectile"):
            if "objects" not in params or not params["objects"]:
                raise ValueError("At least one object required")
        return params

    def _create_object(self, physics_client, obj, restitution, friction):
        shape = obj.get("shape", "sphere")
        mass = obj.get("mass", 1.0)
        position = obj.get("position", [0, 0, 1])
        velocity = obj.get("velocity", [0, 0, 0])
        orientation = obj.get("orientation", [0, 0, 0, 1])
        radius = obj.get("radius", 0.5)
        half_extents = obj.get("half_extents", [0.5, 0.5, 0.5])

        if shape == "sphere":
            col = pb.createCollisionShape(pb.GEOM_SPHERE, radius=radius,
                                          physicsClientId=physics_client)
            vis = pb.createVisualShape(pb.GEOM_SPHERE, radius=radius,
                                       physicsClientId=physics_client)
        elif shape == "box":
            col = pb.createCollisionShape(pb.GEOM_BOX, halfExtents=half_extents,
                                          physicsClientId=physics_client)
            vis = pb.createVisualShape(pb.GEOM_BOX, halfExtents=half_extents,
                                       physicsClientId=physics_client)
        elif shape == "cylinder":
            col = pb.createCollisionShape(pb.GEOM_CYLINDER, radius=radius,
                                          height=obj.get("height", 1.0),
                                          physicsClientId=physics_client)
            vis = pb.createVisualShape(pb.GEOM_CYLINDER, radius=radius,
                                       length=obj.get("height", 1.0),
                                       physicsClientId=physics_client)
        else:
            raise ValueError(f"Unknown shape: {shape}")

        body_id = pb.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=position,
            baseOrientation=orientation,
            physicsClientId=physics_client,
        )
        pb.resetBaseVelocity(body_id, linearVelocity=velocity,
                             physicsClientId=physics_client)
        pb.changeDynamics(body_id, -1, restitution=restitution,
                          lateralFriction=friction,
                          physicsClientId=physics_client)
        return body_id

    def _setup_pendulum(self, physics_client, params):
        length = params.get("pendulum_length", 1.0)
        bob_mass = params.get("bob_mass", 1.0)
        initial_angle = params.get("initial_angle", math.pi / 4)

        # Pivot (fixed)
        pivot_col = pb.createCollisionShape(pb.GEOM_SPHERE, radius=0.05,
                                            physicsClientId=physics_client)
        pivot_id = pb.createMultiBody(baseMass=0, baseCollisionShapeIndex=pivot_col,
                                      basePosition=[0, 0, 2],
                                      physicsClientId=physics_client)

        # Bob
        bob_x = length * math.sin(initial_angle)
        bob_z = 2 - length * math.cos(initial_angle)
        bob_col = pb.createCollisionShape(pb.GEOM_SPHERE, radius=0.1,
                                          physicsClientId=physics_client)
        bob_id = pb.createMultiBody(baseMass=bob_mass, baseCollisionShapeIndex=bob_col,
                                    basePosition=[bob_x, 0, bob_z],
                                    physicsClientId=physics_client)

        # Point-to-point constraint (rope)
        pb.createConstraint(pivot_id, -1, bob_id, -1, pb.JOINT_POINT2POINT,
                            [0, 0, 0], [0, 0, 0],
                            [bob_x, 0, bob_z - 2],
                            physicsClientId=physics_client)
        return [pivot_id, bob_id]

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]
        gravity = params["gravity"]
        timestep = params["timestep"]
        duration = params["duration"]
        restitution = params["restitution"]
        friction = params["friction"]

        physics_client = pb.connect(pb.DIRECT)
        pb.setAdditionalSearchPath(pybullet_data.getDataPath(),
                                   physicsClientId=physics_client)
        pb.setGravity(0, 0, gravity, physicsClientId=physics_client)
        pb.setTimeStep(timestep, physicsClientId=physics_client)

        # Ground plane
        pb.loadURDF("plane.urdf", physicsClientId=physics_client)

        body_ids = []
        object_names = []

        if sim_type == "pendulum":
            body_ids = self._setup_pendulum(physics_client, params)
            object_names = ["pivot", "bob"]
        elif sim_type == "custom_urdf":
            urdf_path = params.get("urdf_path", "")
            if urdf_path:
                body_id = pb.loadURDF(urdf_path, physicsClientId=physics_client)
                body_ids = [body_id]
                object_names = ["urdf_object"]
        else:
            for i, obj in enumerate(params.get("objects", [])):
                body_id = self._create_object(physics_client, obj, restitution, friction)
                body_ids.append(body_id)
                object_names.append(obj.get("name", f"object_{i}"))

        n_steps = int(duration / timestep)
        record_interval = max(1, n_steps // 500)
        frames = []
        energies = []
        collisions = []

        for step in range(n_steps):
            pb.stepSimulation(physicsClientId=physics_client)

            if step % record_interval == 0:
                frame_data = []
                total_ke = 0.0
                total_pe = 0.0

                for body_id in body_ids:
                    pos, orn = pb.getBasePositionAndOrientation(body_id,
                                                                physicsClientId=physics_client)
                    vel, ang_vel = pb.getBaseVelocity(body_id,
                                                      physicsClientId=physics_client)
                    mass_info = pb.getDynamicsInfo(body_id, -1,
                                                   physicsClientId=physics_client)
                    m = mass_info[0]

                    frame_data.append({
                        "position": list(pos),
                        "orientation": list(orn),
                        "velocity": list(vel),
                    })

                    speed_sq = vel[0]**2 + vel[1]**2 + vel[2]**2
                    total_ke += 0.5 * m * speed_sq
                    total_pe += m * abs(gravity) * pos[2]

                frames.append(frame_data)
                energies.append({
                    "time": step * timestep,
                    "kinetic": total_ke,
                    "potential": total_pe,
                    "total": total_ke + total_pe,
                })

            # Check collisions
            contact_points = pb.getContactPoints(physicsClientId=physics_client)
            for cp in contact_points:
                if cp[8] < 0:  # penetration depth < 0 means contact
                    if step % record_interval == 0:
                        collisions.append({
                            "time": step * timestep,
                            "bodyA": cp[1],
                            "bodyB": cp[2],
                            "position": list(cp[5]),
                            "normal_force": cp[9],
                        })

        pb.disconnect(physics_client)

        return {
            "tool": "pybullet",
            "simulation_type": sim_type,
            "object_names": object_names,
            "frames": frames,
            "energies": energies,
            "collisions": collisions,
            "n_objects": len(body_ids),
            "n_steps": len(frames),
            "duration": duration,
            "gravity": gravity,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "collision",
            "gravity": -9.81,
            "timestep": 1.0 / 240.0,
            "duration": 3.0,
            "restitution": 0.9,
            "friction": 0.5,
            "objects": [
                {"name": "sphere_1", "shape": "sphere", "mass": 1.0,
                 "position": [-2, 0, 1], "velocity": [3, 0, 0], "radius": 0.3},
                {"name": "sphere_2", "shape": "sphere", "mass": 1.0,
                 "position": [2, 0, 1], "velocity": [-3, 0, 0], "radius": 0.3},
            ],
        }


@celery_app.task(name="tools.pybullet_tool.run_pybullet", bind=True)
def run_pybullet(self, params: dict, project: str = "_default",
                 label: str | None = None) -> dict:
    tool = PyBulletTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting PyBullet simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})

    save_result(self.request.id, "pybullet", result, project, label)

    return result

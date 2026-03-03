import base64
import io
from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class VTKTool(SimulationTool):
    name = "VTK"
    key = "vtk"
    layer = "visualization"

    SIMULATION_TYPES = {"field_render", "isosurface", "streamlines", "volume_render"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "field_render")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("colormap", "viridis")
        params.setdefault("window_size", [800, 600])
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "field_render":
            return self._run_field_render(params)
        elif sim_type == "isosurface":
            return self._run_isosurface(params)
        elif sim_type == "streamlines":
            return self._run_streamlines(params)
        elif sim_type == "volume_render":
            return self._run_volume_render(params)

    def _setup_offscreen(self):
        """Initialize VTK with OSMesa offscreen rendering."""
        import vtk
        # Enable OSMesa offscreen rendering
        vtk.vtkGraphicsFactory.SetOffScreenOnlyMode(1)
        vtk.vtkGraphicsFactory.SetUseMesaClasses(1)

    def _render_to_png(self, renderer, window_size):
        """Render a VTK scene to a base64 PNG string."""
        import vtk

        render_window = vtk.vtkRenderWindow()
        render_window.SetOffScreenRendering(1)
        render_window.SetSize(window_size[0], window_size[1])
        render_window.AddRenderer(renderer)
        render_window.Render()

        # Capture to PNG via vtkWindowToImageFilter
        window_to_image = vtk.vtkWindowToImageFilter()
        window_to_image.SetInput(render_window)
        window_to_image.SetInputBufferTypeToRGB()
        window_to_image.Update()

        writer = vtk.vtkPNGWriter()
        writer.WriteToMemoryOn()
        writer.SetInputConnection(window_to_image.GetOutputPort())
        writer.Write()

        png_data = bytes(writer.GetResult())
        return base64.b64encode(png_data).decode("ascii")

    def _field_to_vtk_grid(self, field_data, x_grid, y_grid):
        """Convert 2D field data to vtkRectilinearGrid."""
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk

        field = np.array(field_data, dtype=np.float64)
        ny, nx = field.shape

        x_arr = np.array(x_grid, dtype=np.float64) if x_grid else np.linspace(0, 1, nx)
        y_arr = np.array(y_grid, dtype=np.float64) if y_grid else np.linspace(0, 1, ny)
        z_arr = np.array([0.0], dtype=np.float64)

        grid = vtk.vtkRectilinearGrid()
        grid.SetDimensions(len(x_arr), len(y_arr), 1)
        grid.SetXCoordinates(numpy_to_vtk(x_arr))
        grid.SetYCoordinates(numpy_to_vtk(y_arr))
        grid.SetZCoordinates(numpy_to_vtk(z_arr))

        # Flatten field data in VTK order (x varies fastest)
        scalars = numpy_to_vtk(field.flatten(order="C"))
        scalars.SetName("field")
        grid.GetPointData().SetScalars(scalars)

        return grid

    def _apply_colormap(self, mapper, colormap_name):
        """Apply a named colormap to a VTK mapper via lookup table."""
        import vtk

        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)

        # Generate colormap from matplotlib
        try:
            import matplotlib.pyplot as plt
            cmap = plt.get_cmap(colormap_name)
            for i in range(256):
                rgba = cmap(i / 255.0)
                lut.SetTableValue(i, rgba[0], rgba[1], rgba[2], 1.0)
        except Exception:
            lut.SetHueRange(0.667, 0.0)  # fallback: blue-to-red

        lut.Build()
        mapper.SetLookupTable(lut)

    def _run_field_render(self, params):
        """2D heatmap rendering of field data."""
        import vtk

        self._setup_offscreen()

        field_data = params.get("field_data", [[0]])
        x_grid = params.get("x_grid", [])
        y_grid = params.get("y_grid", [])
        colormap = params.get("colormap", "viridis")
        window_size = params.get("window_size", [800, 600])

        grid = self._field_to_vtk_grid(field_data, x_grid, y_grid)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(grid)
        mapper.SetScalarRange(grid.GetScalarRange())
        self._apply_colormap(mapper, colormap)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Add scalar bar (colorbar)
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(mapper.GetLookupTable())
        scalar_bar.SetTitle("Field")
        scalar_bar.SetNumberOfLabels(5)

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.AddActor2D(scalar_bar)
        renderer.SetBackground(0.1, 0.1, 0.15)
        renderer.ResetCamera()

        image_b64 = self._render_to_png(renderer, window_size)

        return {
            "tool": "vtk",
            "simulation_type": "field_render",
            "image_base64": image_b64,
            "image_format": "png",
            "window_size": window_size,
            "colormap": colormap,
        }

    def _run_isosurface(self, params):
        """Extract and render isosurfaces from 3D field data."""
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk

        self._setup_offscreen()

        field_data = params.get("field_data", [[[0]]])
        iso_values = params.get("iso_values", [0.5])
        colormap = params.get("colormap", "viridis")
        window_size = params.get("window_size", [800, 600])

        field = np.array(field_data, dtype=np.float64)

        # Handle 2D data by expanding to 3D
        if field.ndim == 2:
            field = field[np.newaxis, :, :]

        nz, ny, nx = field.shape

        # Build structured grid
        image_data = vtk.vtkImageData()
        image_data.SetDimensions(nx, ny, nz)
        image_data.SetSpacing(1.0 / max(nx - 1, 1), 1.0 / max(ny - 1, 1), 1.0 / max(nz - 1, 1))

        scalars = numpy_to_vtk(field.flatten(order="C"))
        scalars.SetName("field")
        image_data.GetPointData().SetScalars(scalars)

        # Contour filter for isosurfaces
        contour = vtk.vtkContourFilter()
        contour.SetInputData(image_data)
        for i, val in enumerate(iso_values):
            contour.SetValue(i, float(val))
        contour.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())
        mapper.SetScalarRange(float(np.min(field)), float(np.max(field)))
        self._apply_colormap(mapper, colormap)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(0.7)

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(0.1, 0.1, 0.15)
        renderer.ResetCamera()

        image_b64 = self._render_to_png(renderer, window_size)

        return {
            "tool": "vtk",
            "simulation_type": "isosurface",
            "image_base64": image_b64,
            "image_format": "png",
            "iso_values": iso_values,
            "window_size": window_size,
            "colormap": colormap,
        }

    def _run_streamlines(self, params):
        """Render streamlines from vector field data."""
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk

        self._setup_offscreen()

        field_data = params.get("field_data", [[0]])
        x_grid = params.get("x_grid", [])
        y_grid = params.get("y_grid", [])
        seed_points = params.get("seed_points", [])
        colormap = params.get("colormap", "viridis")
        window_size = params.get("window_size", [800, 600])

        field = np.array(field_data, dtype=np.float64)
        ny, nx = field.shape

        x_arr = np.array(x_grid, dtype=np.float64) if x_grid else np.linspace(0, 1, nx)
        y_arr = np.array(y_grid, dtype=np.float64) if y_grid else np.linspace(0, 1, ny)

        # Build a vector field from scalar gradient
        grid = vtk.vtkRectilinearGrid()
        grid.SetDimensions(len(x_arr), len(y_arr), 1)
        grid.SetXCoordinates(numpy_to_vtk(x_arr))
        grid.SetYCoordinates(numpy_to_vtk(y_arr))
        grid.SetZCoordinates(numpy_to_vtk(np.array([0.0])))

        # Compute gradient as vector field
        gy, gx = np.gradient(field)
        vectors = np.zeros((ny * nx, 3), dtype=np.float64)
        vectors[:, 0] = gx.flatten()
        vectors[:, 1] = gy.flatten()
        vtk_vectors = numpy_to_vtk(vectors)
        vtk_vectors.SetName("vectors")
        grid.GetPointData().SetVectors(vtk_vectors)

        # Scalar magnitude
        mag = np.sqrt(gx**2 + gy**2).flatten()
        scalars = numpy_to_vtk(mag)
        scalars.SetName("magnitude")
        grid.GetPointData().SetScalars(scalars)

        # Seed points for streamlines
        seeds = vtk.vtkPointSource()
        if seed_points:
            seed_pts = vtk.vtkPoints()
            for sp in seed_points:
                seed_pts.InsertNextPoint(sp[0], sp[1], 0.0)
            seed_data = vtk.vtkPolyData()
            seed_data.SetPoints(seed_pts)
        else:
            seeds.SetCenter((x_arr[0] + x_arr[-1]) / 2, (y_arr[0] + y_arr[-1]) / 2, 0)
            seeds.SetRadius(min(x_arr[-1] - x_arr[0], y_arr[-1] - y_arr[0]) * 0.3)
            seeds.SetNumberOfPoints(20)
            seeds.Update()
            seed_data = seeds.GetOutput()

        tracer = vtk.vtkStreamTracer()
        tracer.SetInputData(grid)
        tracer.SetSourceData(seed_data)
        tracer.SetMaximumPropagation(max(x_arr[-1], y_arr[-1]) * 2)
        tracer.SetIntegrationDirectionToForward()
        tracer.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(tracer.GetOutputPort())
        if tracer.GetOutput().GetPointData().GetScalars():
            mapper.SetScalarRange(tracer.GetOutput().GetPointData().GetScalars().GetRange())
        self._apply_colormap(mapper, colormap)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(0.1, 0.1, 0.15)
        renderer.ResetCamera()

        image_b64 = self._render_to_png(renderer, window_size)

        return {
            "tool": "vtk",
            "simulation_type": "streamlines",
            "image_base64": image_b64,
            "image_format": "png",
            "window_size": window_size,
            "colormap": colormap,
        }

    def _run_volume_render(self, params):
        """Volume rendering of 3D field data."""
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk

        self._setup_offscreen()

        field_data = params.get("field_data", [[[0]]])
        colormap = params.get("colormap", "viridis")
        window_size = params.get("window_size", [800, 600])

        field = np.array(field_data, dtype=np.float64)
        if field.ndim == 2:
            field = field[np.newaxis, :, :]
        nz, ny, nx = field.shape

        image_data = vtk.vtkImageData()
        image_data.SetDimensions(nx, ny, nz)
        image_data.SetSpacing(1.0 / max(nx - 1, 1), 1.0 / max(ny - 1, 1), 1.0 / max(nz - 1, 1))

        scalars = numpy_to_vtk(field.flatten(order="C"))
        scalars.SetName("field")
        image_data.GetPointData().SetScalars(scalars)

        # Volume rendering pipeline
        volume_mapper = vtk.vtkSmartVolumeMapper()
        volume_mapper.SetInputData(image_data)

        # Transfer functions
        scalar_range = [float(np.min(field)), float(np.max(field))]
        mid = (scalar_range[0] + scalar_range[1]) / 2

        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(scalar_range[0], 0.0)
        opacity_tf.AddPoint(mid, 0.3)
        opacity_tf.AddPoint(scalar_range[1], 0.8)

        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(scalar_range[0], 0.0, 0.0, 0.5)
        color_tf.AddRGBPoint(mid, 0.0, 0.8, 0.0)
        color_tf.AddRGBPoint(scalar_range[1], 0.8, 0.0, 0.0)

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.SetColor(color_tf)
        volume_property.SetInterpolationTypeToLinear()

        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)

        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)
        renderer.SetBackground(0.1, 0.1, 0.15)
        renderer.ResetCamera()

        image_b64 = self._render_to_png(renderer, window_size)

        return {
            "tool": "vtk",
            "simulation_type": "volume_render",
            "image_base64": image_b64,
            "image_format": "png",
            "window_size": window_size,
            "colormap": colormap,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "field_render",
            "field_data": [[float(np.sin(x / 5) * np.cos(y / 5)) for x in range(32)] for y in range(32)],
            "x_grid": list(np.linspace(0, 1, 32)),
            "y_grid": list(np.linspace(0, 1, 32)),
            "colormap": "viridis",
            "window_size": [800, 600],
        }


@celery_app.task(name="tools.vtk_tool.run_vtk", bind=True)
def run_vtk(self, params: dict, project: str = "_default",
            label: str | None = None) -> dict:
    tool = VTKTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting VTK rendering"})

    try:
        sim_type = params.get("simulation_type", "field_render")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Rendering {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "vtk", result, project, label)

    return result

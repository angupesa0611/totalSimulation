import { describe, it, expect } from 'vitest';
import { toolDocs, allToolKeys, getToolsByLayer, searchTools } from '../toolDocs';
import { couplingDocs, searchCouplings } from '../couplingDocs';
import { pipelineDocs, allPipelineKeys, searchPipelines } from '../pipelineDocs';

// All 55 tool keys expected in the platform
const EXPECTED_TOOL_KEYS = [
  'rebound', 'qutip', 'openmm', 'pyscf', 'mdanalysis', 'psi4', 'gromacs', 'namd',
  'qmmm', 'pybullet', 'einsteinpy', 'nrpy', 'fenics', 'elmer', 'basico', 'tellurium',
  'brian2', 'nest', 'msprime', 'rdkit', 'cantera', 'qe', 'lammps', 'sympy', 'gmsh',
  'lcapy', 'pennylane', 'sagemath', 'lean4', 'gap', 'pyspice', 'qiskit', 'matplotlib',
  'control', 'pyomo', 'networkx', 'phiflow', 'manim', 'openfoam', 'dedalus', 'su2',
  'firedrake', 'vtk', 'openbabel', 'comsol', 'alphafold', 'slim', 'tskit', 'simupop',
  'pyrosetta', 'einstein_toolkit', 'rayoptics', 'lightpipes', 'strawberryfields', 'meep',
];

const REQUIRED_TOOL_FIELDS = ['name', 'layer', 'summary', 'description'];

describe('toolDocs', () => {
  it('has entries for all 55 expected tools', () => {
    for (const key of EXPECTED_TOOL_KEYS) {
      expect(toolDocs).toHaveProperty(key);
    }
  });

  it('has exactly 55 tools', () => {
    expect(allToolKeys.length).toBe(55);
  });

  it('every tool has required fields', () => {
    for (const [key, doc] of Object.entries(toolDocs)) {
      for (const field of REQUIRED_TOOL_FIELDS) {
        expect(doc, `${key} missing ${field}`).toHaveProperty(field);
        expect(doc[field], `${key}.${field} should be non-empty`).toBeTruthy();
      }
    }
  });

  it('every tool has a valid layer', () => {
    const validLayers = [
      'astrophysics', 'quantum', 'molecular', 'electronic', 'analysis', 'multiscale',
      'mechanics', 'continuum', 'relativity', 'systems-biology', 'neuroscience',
      'evolution', 'chemistry', 'materials', 'mathematics', 'circuits',
      'visualization', 'fluid-dynamics', 'engineering', 'optics',
    ];
    for (const [key, doc] of Object.entries(toolDocs)) {
      expect(validLayers, `${key} has invalid layer: ${doc.layer}`).toContain(doc.layer);
    }
  });

  it('getToolsByLayer groups correctly', () => {
    const groups = getToolsByLayer();
    expect(Object.keys(groups).length).toBeGreaterThan(0);
    let totalTools = 0;
    for (const tools of Object.values(groups)) {
      totalTools += tools.length;
    }
    expect(totalTools).toBe(55);
  });

  it('searchTools returns all tools for empty query', () => {
    expect(searchTools('').length).toBe(55);
  });

  it('searchTools filters by name', () => {
    const results = searchTools('rebound');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].key).toBe('rebound');
  });

  it('searchTools filters by layer', () => {
    const results = searchTools('astrophysics');
    expect(results.length).toBeGreaterThan(0);
    expect(results.every(r => r.layer === 'astrophysics')).toBe(true);
  });
});

describe('couplingDocs', () => {
  it('has coupling categories', () => {
    expect(couplingDocs.categories.length).toBeGreaterThan(10);
  });

  it('every category has required fields', () => {
    for (const cat of couplingDocs.categories) {
      expect(cat).toHaveProperty('id');
      expect(cat).toHaveProperty('label');
      expect(cat).toHaveProperty('description');
      expect(cat).toHaveProperty('tools');
      expect(cat).toHaveProperty('examples');
      expect(cat.tools.length).toBeGreaterThan(0);
      expect(cat.examples.length).toBeGreaterThan(0);
    }
  });

  it('has detail entries for key couplings', () => {
    expect(Object.keys(couplingDocs.details).length).toBeGreaterThan(5);
  });

  it('every detail entry has required fields', () => {
    for (const [key, detail] of Object.entries(couplingDocs.details)) {
      expect(detail, `${key} missing from`).toHaveProperty('from');
      expect(detail, `${key} missing to`).toHaveProperty('to');
      expect(detail, `${key} missing type`).toHaveProperty('type');
      expect(detail, `${key} missing description`).toHaveProperty('description');
    }
  });

  it('searchCouplings returns all for empty query', () => {
    expect(searchCouplings('').length).toBe(couplingDocs.categories.length);
  });
});

describe('pipelineDocs', () => {
  it('has 11 pipelines', () => {
    expect(allPipelineKeys.length).toBe(12);
  });

  it('every pipeline has required fields', () => {
    for (const [key, doc] of Object.entries(pipelineDocs)) {
      expect(doc, `${key} missing label`).toHaveProperty('label');
      expect(doc, `${key} missing summary`).toHaveProperty('summary');
      expect(doc, `${key} missing steps`).toHaveProperty('steps');
      expect(doc, `${key} missing scientificContext`).toHaveProperty('scientificContext');
      expect(doc.steps.length, `${key} has no steps`).toBeGreaterThan(0);
    }
  });

  it('every pipeline step has tool and role', () => {
    for (const [key, doc] of Object.entries(pipelineDocs)) {
      for (const step of doc.steps) {
        expect(step, `${key} step missing tool`).toHaveProperty('tool');
        expect(step, `${key} step missing role`).toHaveProperty('role');
        expect(step.tool, `${key} step has empty tool`).toBeTruthy();
      }
    }
  });

  it('searchPipelines returns all for empty query', () => {
    expect(searchPipelines('').length).toBe(12);
  });

  it('searchPipelines filters by tool name', () => {
    const results = searchPipelines('qutip');
    expect(results.length).toBeGreaterThan(0);
  });
});

/**
 * Trajectory utilities for MolStar integration.
 * Converts simulation result frames to PDB strings for Mol* loading.
 */

/**
 * Convert a single frame of positions to PDB format.
 * @param {number[][]} positions - Array of [x, y, z] coordinates
 * @param {string[]} atomNames - Atom names (optional)
 * @param {string[]} resnames - Residue names (optional)
 * @returns {string} PDB format string
 */
export function frameToPDB(positions, atomNames, resnames) {
  const lines = [];
  for (let i = 0; i < positions.length; i++) {
    const [x, y, z] = positions[i];
    const name = atomNames?.[i] || 'C';
    const resname = resnames?.[i] || 'UNK';
    const serial = (i + 1) % 100000;
    const resid = Math.min(Math.floor(i / 4) + 1, 9999);
    const paddedName = name.length < 4 ? ` ${name}` : name;

    lines.push(
      `ATOM  ${String(serial).padStart(5)}` +
      ` ${paddedName.padEnd(4)}` +
      ` ${resname.padStart(3)}` +
      ` A${String(resid).padStart(4)}    ` +
      `${x.toFixed(3).padStart(8)}` +
      `${y.toFixed(3).padStart(8)}` +
      `${z.toFixed(3).padStart(8)}` +
      `  1.00  0.00`
    );
  }
  lines.push('END');
  return lines.join('\n');
}

/**
 * Convert multiple frames to a multi-model PDB string.
 * @param {number[][][]} frames - Array of frames, each frame is positions array
 * @param {string[]} atomNames
 * @param {string[]} resnames
 * @returns {string}
 */
export function framesToMultiModelPDB(frames, atomNames, resnames) {
  const lines = [];
  for (let modelIdx = 0; modelIdx < frames.length; modelIdx++) {
    lines.push(`MODEL     ${modelIdx + 1}`);
    const positions = frames[modelIdx];
    for (let i = 0; i < positions.length; i++) {
      const [x, y, z] = positions[i];
      const name = atomNames?.[i] || 'C';
      const resname = resnames?.[i] || 'UNK';
      const serial = (i + 1) % 100000;
      const resid = Math.min(Math.floor(i / 4) + 1, 9999);
      const paddedName = name.length < 4 ? ` ${name}` : name;

      lines.push(
        `ATOM  ${String(serial).padStart(5)}` +
        ` ${paddedName.padEnd(4)}` +
        ` ${resname.padStart(3)}` +
        ` A${String(resid).padStart(4)}    ` +
        `${x.toFixed(3).padStart(8)}` +
        `${y.toFixed(3).padStart(8)}` +
        `${z.toFixed(3).padStart(8)}` +
        `  1.00  0.00`
      );
    }
    lines.push('ENDMDL');
  }
  lines.push('END');
  return lines.join('\n');
}

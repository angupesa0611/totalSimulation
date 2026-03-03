import React, { useCallback, useEffect, useRef, useState } from 'react';
import theme from '../../theme.json';

/**
 * Reusable playback controls for trajectory visualization.
 * Provides play/pause, frame scrubbing, speed control, and frame counter.
 */
export default function PlaybackControls({
  totalFrames,
  currentFrame,
  onFrameChange,
  fps = 20,
}) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        onFrameChange((prev) => {
          const next = prev + 1;
          if (next >= totalFrames) {
            setPlaying(false);
            return 0;
          }
          return next;
        });
      }, 1000 / (fps * speed));
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, speed, fps, totalFrames, onFrameChange]);

  const togglePlay = useCallback(() => {
    if (currentFrame >= totalFrames - 1) {
      onFrameChange(0);
    }
    setPlaying((p) => !p);
  }, [currentFrame, totalFrames, onFrameChange]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '8px 16px',
      background: theme.colors.bgSecondary,
      borderTop: `1px solid ${theme.colors.border}`,
    }}>
      <button
        onClick={togglePlay}
        style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          border: `1px solid ${theme.colors.border}`,
          background: theme.colors.bgTertiary,
          color: theme.colors.text,
          cursor: 'pointer',
          fontSize: 14,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {playing ? '||' : '>'}
      </button>

      <input
        type="range"
        min={0}
        max={Math.max(totalFrames - 1, 0)}
        value={currentFrame}
        onChange={(e) => {
          setPlaying(false);
          onFrameChange(parseInt(e.target.value));
        }}
        style={{ flex: 1, accentColor: theme.colors.accent }}
      />

      <span style={{
        fontSize: 11,
        color: theme.colors.textSecondary,
        fontFamily: theme.fonts.mono,
        minWidth: 80,
        textAlign: 'right',
      }}>
        {currentFrame + 1} / {totalFrames}
      </span>

      <select
        value={speed}
        onChange={(e) => setSpeed(parseFloat(e.target.value))}
        style={{
          background: theme.colors.bgTertiary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 4,
          color: theme.colors.text,
          fontSize: 11,
          padding: '2px 4px',
        }}
      >
        <option value={0.5}>0.5x</option>
        <option value={1}>1x</option>
        <option value={2}>2x</option>
        <option value={5}>5x</option>
      </select>
    </div>
  );
}

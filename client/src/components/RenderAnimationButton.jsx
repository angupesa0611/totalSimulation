import React, { useState, useEffect } from 'react';
import { useRender } from '../hooks/useRender';
import VideoPlayer from '../visualizers/VideoPlayer';
import theme from '../theme.json';

const ACCENT = '#f472b6';

export default function RenderAnimationButton({ toolKey, jobId }) {
  const render = useRender();
  const [sceneType, setSceneType] = useState('');
  const [quality, setQuality] = useState('medium_quality');
  const [expanded, setExpanded] = useState(false);
  const [showVideo, setShowVideo] = useState(false);

  // Load available scenes when tool changes
  useEffect(() => {
    if (toolKey) {
      render.loadScenes(toolKey);
      setExpanded(false);
      setShowVideo(false);
    }
  }, [toolKey]);

  // Auto-select first scene
  useEffect(() => {
    if (render.scenes.length > 0 && !sceneType) {
      setSceneType(render.scenes[0].scene_type);
    }
  }, [render.scenes, sceneType]);

  // Show video when render completes
  useEffect(() => {
    if (render.isDone && render.result) {
      setShowVideo(true);
    }
  }, [render.isDone, render.result]);

  // Don't render button if no scenes available
  if (render.scenes.length === 0 && !render.scenesLoading) {
    return null;
  }

  const handleRender = () => {
    if (!jobId) return;
    render.startRender(jobId, {
      scene_type: sceneType,
      quality,
      format: 'mp4',
    });
  };

  // Show inline video player when render is done
  if (showVideo && render.result) {
    return (
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        zIndex: 20,
        background: '#0a0a0f',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 16px',
          background: '#12121a',
          borderBottom: '1px solid #2a2a3a',
        }}>
          <span style={{ fontSize: 13, color: ACCENT, fontWeight: 600 }}>
            Rendered Animation
          </span>
          <button
            onClick={() => { setShowVideo(false); render.resetRender(); }}
            style={{
              background: 'none', border: `1px solid ${ACCENT}`,
              color: ACCENT, fontSize: 11, padding: '3px 10px',
              borderRadius: 4, cursor: 'pointer',
            }}
          >
            Back to Visualizer
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <VideoPlayer data={render.result} />
        </div>
      </div>
    );
  }

  return (
    <div style={{
      position: 'absolute',
      top: 12,
      right: 12,
      zIndex: 10,
    }}>
      {/* Floating action button */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          title="Render Animation"
          style={{
            width: 40, height: 40,
            borderRadius: '50%',
            background: ACCENT,
            border: 'none',
            color: '#fff',
            fontSize: 18,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
          }}
        >
          &#9654;
        </button>
      )}

      {/* Expanded panel */}
      {expanded && (
        <div style={{
          width: 260,
          background: theme.colors.bgSecondary,
          border: `1px solid ${ACCENT}44`,
          borderRadius: 8,
          padding: 12,
          boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 10,
          }}>
            <span style={{ fontSize: 13, color: ACCENT, fontWeight: 600 }}>
              Render Animation
            </span>
            <button
              onClick={() => setExpanded(false)}
              style={{
                background: 'none', border: 'none',
                color: theme.colors.textSecondary,
                fontSize: 14, cursor: 'pointer',
              }}
            >
              x
            </button>
          </div>

          {/* Scene type selector */}
          {render.scenes.length > 1 && (
            <div style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
                Scene Type
              </label>
              <select
                value={sceneType}
                onChange={(e) => setSceneType(e.target.value)}
                style={{
                  width: '100%', padding: '5px 8px',
                  background: theme.colors.bgTertiary,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: 4, color: theme.colors.text,
                  fontSize: 12,
                }}
              >
                {render.scenes.map(s => (
                  <option key={s.scene_type} value={s.scene_type}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Quality selector */}
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Quality
            </label>
            <div style={{ display: 'flex', gap: 4 }}>
              {['low_quality', 'medium_quality', 'high_quality'].map(q => (
                <button
                  key={q}
                  onClick={() => setQuality(q)}
                  style={{
                    flex: 1, padding: '4px 0',
                    background: quality === q ? ACCENT : theme.colors.bgTertiary,
                    border: `1px solid ${quality === q ? ACCENT : theme.colors.border}`,
                    borderRadius: 4,
                    color: quality === q ? '#fff' : theme.colors.textSecondary,
                    fontSize: 10, cursor: 'pointer',
                  }}
                >
                  {q === 'low_quality' ? '480p' : q === 'medium_quality' ? '720p' : '1080p'}
                </button>
              ))}
            </div>
          </div>

          {/* Render button */}
          <button
            onClick={handleRender}
            disabled={render.isRendering || !sceneType}
            style={{
              width: '100%', padding: '8px 0',
              background: render.isRendering ? theme.colors.bgTertiary : ACCENT,
              border: 'none', borderRadius: 6,
              color: '#fff', fontSize: 12, fontWeight: 600,
              cursor: render.isRendering ? 'default' : 'pointer',
              opacity: render.isRendering ? 0.7 : 1,
            }}
          >
            {render.isRendering ? 'Rendering...' : 'Render Animation'}
          </button>

          {/* Progress bar */}
          {render.isRendering && (
            <div style={{ marginTop: 8 }}>
              <div style={{
                height: 4, background: theme.colors.bgTertiary,
                borderRadius: 2, overflow: 'hidden',
              }}>
                <div style={{
                  width: `${(render.progress || 0) * 100}%`,
                  height: '100%', background: ACCENT,
                  borderRadius: 2, transition: 'width 0.3s',
                }} />
              </div>
              <div style={{ fontSize: 10, color: theme.colors.textSecondary, marginTop: 4 }}>
                {render.message || 'Processing...'}
              </div>
            </div>
          )}

          {/* Error */}
          {render.isFailed && (
            <div style={{
              marginTop: 8, padding: 8,
              background: '#1a0a0a', borderRadius: 4,
              border: '1px solid #ef4444',
              fontSize: 11, color: '#ef4444',
            }}>
              {render.error || 'Render failed'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { getLayers, getCouplings, getPipelines, getPresets, getPresetParams } from '../api/client';
import ResultsBrowser from './ResultsBrowser';
import ToolPreview from './ToolPreview';
import PipelinePreview from './PipelinePreview';
import theme from '../theme.json';

const layerColors = theme.colors.layers;

// --- Section header with collapse toggle and count badge ---
function SectionHeader({ title, count, collapsed, onToggle, color }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '16px 0 10px',
        width: '100%',
        textAlign: 'left',
        opacity: hovered ? 1 : 0.85,
        transition: 'opacity 0.2s ease-out',
      }}
    >
      <span style={{
        fontSize: 10,
        color: color || 'rgba(255,255,255,0.35)',
        transition: 'transform 0.2s ease-out',
        transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
        display: 'inline-block',
      }}>
        {'\u25BC'}
      </span>
      <span style={{
        fontSize: 13,
        fontWeight: 600,
        color: color || theme.colors.text,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}>
        {title}
      </span>
      {count !== '' && (
        <span style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.4)',
          background: 'rgba(255,255,255,0.06)',
          padding: '2px 10px',
          borderRadius: 9999,
          fontWeight: 500,
        }}>
          {count}
        </span>
      )}
      <div style={{
        flex: 1,
        height: 1,
        background: 'rgba(255,255,255,0.06)',
        marginLeft: 8,
      }} />
    </button>
  );
}

// --- Layer dropdown header ---
function LayerHeader({ name, color, count, collapsed, onToggle }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: hovered ? 'rgba(255,255,255,0.03)' : 'transparent',
        border: 'none',
        cursor: 'pointer',
        padding: '10px 12px',
        width: '100%',
        textAlign: 'left',
        borderRadius: 8,
        transition: 'background 0.2s ease-out',
      }}
    >
      <span style={{
        fontSize: 9,
        color: 'rgba(255,255,255,0.3)',
        transition: 'transform 0.2s ease-out',
        transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
        display: 'inline-block',
      }}>
        {'\u25BC'}
      </span>
      <span style={{
        width: 10,
        height: 10,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 8px ${color}40`,
        flexShrink: 0,
      }} />
      <span style={{
        fontSize: 13,
        fontWeight: 600,
        color,
        letterSpacing: '0.01em',
      }}>
        {name}
      </span>
      <span style={{
        fontSize: 10,
        color: 'rgba(255,255,255,0.35)',
        background: 'rgba(255,255,255,0.05)',
        padding: '1px 8px',
        borderRadius: 9999,
        fontWeight: 500,
        marginLeft: 'auto',
      }}>
        {count}
      </span>
    </button>
  );
}

// --- Tool card ---
function ToolCard({ tool, layerColor, onClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: 200,
        padding: '14px 16px',
        background: hovered ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.025)',
        border: `1px solid ${hovered ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)'}`,
        borderLeft: `3px solid ${layerColor}`,
        borderRadius: 12,
        color: theme.colors.text,
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 0.2s ease-out',
        flexShrink: 0,
        transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered
          ? `0 8px 24px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.06), 0 4px 12px ${layerColor}15`
          : '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{
        fontSize: 13,
        fontWeight: 600,
        marginBottom: 6,
        letterSpacing: '0.01em',
      }}>
        {tool.name}
      </div>
      <div style={{
        fontSize: 11,
        color: 'rgba(255,255,255,0.45)',
        lineHeight: 1.5,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {tool.description}
      </div>
    </button>
  );
}

// --- Preset card ---
function PresetCard({ preset, onClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: 200,
        padding: '14px 16px',
        background: hovered ? 'rgba(99,102,241,0.1)' : 'rgba(99,102,241,0.04)',
        border: `1px solid ${hovered ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.12)'}`,
        borderRadius: 12,
        color: theme.colors.text,
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 0.2s ease-out',
        flexShrink: 0,
        transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered
          ? '0 8px 24px rgba(0,0,0,0.3), 0 4px 12px rgba(99,102,241,0.15)'
          : '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <span style={{
          fontSize: 9,
          color: theme.colors.accent,
          background: 'rgba(99,102,241,0.15)',
          padding: '2px 7px',
          borderRadius: 9999,
          fontWeight: 600,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
        }}>
          Preset
        </span>
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, letterSpacing: '0.01em' }}>
        {preset.label}
      </div>
      <div style={{
        fontSize: 11,
        color: 'rgba(255,255,255,0.45)',
        lineHeight: 1.5,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {preset.description}
      </div>
    </button>
  );
}

// --- Pipeline card ---
function PipelineCard({ pipelineKey, pipeline, onClick }) {
  const [hovered, setHovered] = useState(false);
  const teal = '#14b8a6';
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: 240,
        padding: '16px 18px',
        background: hovered ? 'rgba(20,184,166,0.08)' : 'rgba(20,184,166,0.03)',
        border: `1px solid ${hovered ? 'rgba(20,184,166,0.3)' : 'rgba(20,184,166,0.1)'}`,
        borderRadius: 12,
        color: theme.colors.text,
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 0.2s ease-out',
        flexShrink: 0,
        transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered
          ? `0 8px 24px rgba(0,0,0,0.3), 0 4px 12px ${teal}20`
          : '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '0.01em' }}>
          {pipeline.label}
        </span>
        <span style={{
          fontSize: 10,
          color: teal,
          background: `${teal}18`,
          padding: '2px 8px',
          borderRadius: 9999,
          fontWeight: 600,
          border: `1px solid ${teal}25`,
        }}>
          {pipeline.n_steps} steps
        </span>
      </div>
      <div style={{
        fontSize: 11,
        color: 'rgba(255,255,255,0.45)',
        lineHeight: 1.5,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {pipeline.description}
      </div>
    </button>
  );
}

// --- Coupling chip ---
function CouplingChip({ coupling, couplingKey, onClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '7px 14px',
        background: hovered ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.025)',
        border: `1px solid ${hovered ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)'}`,
        borderRadius: 9999,
        color: theme.colors.text,
        cursor: 'pointer',
        transition: 'all 0.2s ease-out',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 12,
        transform: hovered ? 'translateY(-1px)' : 'translateY(0)',
        boxShadow: hovered ? '0 4px 12px rgba(0,0,0,0.2)' : 'none',
      }}
    >
      <span style={{ fontWeight: 600, fontSize: 11 }}>{coupling.from}</span>
      <span style={{ color: 'rgba(255,255,255,0.25)', fontSize: 12 }}>{'\u2192'}</span>
      <span style={{ fontWeight: 600, fontSize: 11 }}>{coupling.to}</span>
      <span style={{
        fontSize: 9,
        color: theme.colors.accent,
        background: 'rgba(99,102,241,0.12)',
        padding: '1px 6px',
        borderRadius: 9999,
        fontWeight: 500,
        border: '1px solid rgba(99,102,241,0.2)',
      }}>
        {coupling.type}
      </span>
    </button>
  );
}

// --- Sweep action card ---
function SweepCard({ onClick }) {
  const [hovered, setHovered] = useState(false);
  const amber = theme.colors.warning;
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: 260,
        padding: '20px 20px',
        background: hovered ? 'rgba(245,158,11,0.08)' : 'rgba(245,158,11,0.03)',
        border: `1px solid ${hovered ? 'rgba(245,158,11,0.3)' : 'rgba(245,158,11,0.1)'}`,
        borderRadius: 12,
        color: theme.colors.text,
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 0.2s ease-out',
        transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered
          ? `0 8px 24px rgba(0,0,0,0.3), 0 4px 12px ${amber}20`
          : '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{
          fontSize: 18,
          lineHeight: 1,
        }}>
          {'\u2B21'}
        </span>
        <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '0.01em' }}>
          Parameter Sweep
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 1.5 }}>
        Sweep parameters across ranges to explore tool behavior
      </div>
    </button>
  );
}

const COUPLING_INITIAL_SHOW = 24;

export default function Dashboard({
  onSelectTool,
  onLoadPreset,
  onSelectPipeline,
  onSelectCoupling,
  onSelectSweep,
  onSelectResult,
  project,
  isMobile,
}) {
  const [layers, setLayers] = useState([]);
  const [couplings, setCouplings] = useState({});
  const [pipelines, setPipelines] = useState({});
  const [presets, setPresets] = useState([]);
  const [search, setSearch] = useState('');
  const [collapsed, setCollapsed] = useState({});
  const [collapsedLayers, setCollapsedLayers] = useState({});
  const [showAllCouplings, setShowAllCouplings] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [previewTool, setPreviewTool] = useState(null);
  const [previewPipeline, setPreviewPipeline] = useState(null);

  useEffect(() => {
    getLayers().then(setLayers).catch(console.error);
    getCouplings().then(setCouplings).catch(console.error);
    getPipelines().then(setPipelines).catch(console.error);
    getPresets().then(setPresets).catch(console.error);
  }, []);

  const toggleSection = (key) => setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));
  const toggleLayer = (key) => setCollapsedLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const q = search.toLowerCase().trim();

  const filteredLayers = useMemo(() => {
    if (!q) return layers;
    return layers.map(layer => ({
      ...layer,
      tools: layer.tools.filter(t =>
        t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q)
      ),
    })).filter(layer => layer.tools.length > 0);
  }, [layers, q]);

  const totalTools = useMemo(() => filteredLayers.reduce((sum, l) => sum + l.tools.length, 0), [filteredLayers]);

  const filteredPresets = useMemo(() => {
    if (!q) return presets;
    return presets.filter(p =>
      p.label.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q)
    );
  }, [presets, q]);

  const filteredPipelines = useMemo(() => {
    const entries = Object.entries(pipelines);
    if (!q) return entries;
    return entries.filter(([key, p]) =>
      p.label.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q) || key.toLowerCase().includes(q)
    );
  }, [pipelines, q]);

  const filteredCouplings = useMemo(() => {
    const entries = Object.entries(couplings);
    if (!q) return entries;
    return entries.filter(([key, c]) =>
      c.from.toLowerCase().includes(q) || c.to.toLowerCase().includes(q) ||
      key.toLowerCase().includes(q) || (c.type || '').toLowerCase().includes(q)
    );
  }, [couplings, q]);

  const visibleCouplings = showAllCouplings ? filteredCouplings : filteredCouplings.slice(0, COUPLING_INITIAL_SHOW);

  const handlePresetClick = async (preset) => {
    try {
      const params = await getPresetParams(preset.key);
      onLoadPreset(params);
    } catch (err) {
      console.error('Failed to load preset:', err);
    }
  };

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: isMobile ? '16px 12px' : '28px 32px',
      background: theme.colors.bg,
    }}>
      {/* Search bar */}
      <div style={{
        maxWidth: 560,
        margin: '0 auto 28px',
        position: 'relative',
      }}>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
          placeholder="Search tools, pipelines, couplings..."
          style={{
            width: '100%',
            padding: '12px 18px 12px 42px',
            background: 'rgba(255,255,255,0.04)',
            border: `1px solid ${searchFocused ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: 12,
            color: theme.colors.text,
            fontSize: 14,
            outline: 'none',
            boxSizing: 'border-box',
            boxShadow: searchFocused
              ? '0 0 0 3px rgba(99,102,241,0.12), inset 0 2px 4px rgba(0,0,0,0.2)'
              : 'inset 0 2px 4px rgba(0,0,0,0.15)',
            transition: 'all 0.2s ease-out',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
          }}
        />
        <span style={{
          position: 'absolute',
          left: 14,
          top: '50%',
          transform: 'translateY(-50%)',
          color: searchFocused ? theme.colors.accent : 'rgba(255,255,255,0.3)',
          fontSize: 16,
          pointerEvents: 'none',
          transition: 'color 0.2s ease-out',
        }}>
          {'\u2315'}
        </span>
      </div>

      {/* Tools Section */}
      <SectionHeader
        title="Tools"
        count={totalTools}
        collapsed={collapsed.tools}
        onToggle={() => toggleSection('tools')}
      />
      {!collapsed.tools && (
        <div style={{ marginBottom: 32 }}>
          {filteredLayers.map(layer => {
            const color = layerColors[layer.key] || theme.colors.accent;
            const isLayerCollapsed = collapsedLayers[layer.key];
            return (
              <div key={layer.key} style={{ marginBottom: 2 }}>
                <LayerHeader
                  name={layer.name}
                  color={color}
                  count={layer.tools.length}
                  collapsed={isLayerCollapsed}
                  onToggle={() => toggleLayer(layer.key)}
                />
                {!isLayerCollapsed && (
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 10,
                    padding: '8px 12px 16px 36px',
                  }}>
                    {layer.tools.map(tool => (
                      <ToolCard
                        key={tool.key}
                        tool={tool}
                        layerColor={color}
                        onClick={() => setPreviewTool(tool)}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Presets subsection */}
          {filteredPresets.length > 0 && (() => {
            const isPresetsCollapsed = collapsedLayers._presets;
            return (
              <div style={{ marginTop: 2 }}>
                <LayerHeader
                  name="Presets"
                  color={theme.colors.accent}
                  count={filteredPresets.length}
                  collapsed={isPresetsCollapsed}
                  onToggle={() => toggleLayer('_presets')}
                />
                {!isPresetsCollapsed && (
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 10,
                    padding: '8px 12px 16px 36px',
                  }}>
                    {filteredPresets.map(preset => {
                      const toolMatch = layers.flatMap(l => l.tools).find(t => t.key === preset.tool);
                      return (
                        <PresetCard
                          key={preset.key}
                          preset={preset}
                          onClick={() => {
                            if (toolMatch) {
                              setPreviewTool({ ...toolMatch, _presetKey: preset.key });
                            } else {
                              handlePresetClick(preset);
                            }
                          }}
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Pipelines Section */}
      <SectionHeader
        title="Pipelines"
        count={filteredPipelines.length}
        collapsed={collapsed.pipelines}
        onToggle={() => toggleSection('pipelines')}
        color="#14b8a6"
      />
      {!collapsed.pipelines && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 32,
          padding: '4px 0 4px 28px',
        }}>
          {filteredPipelines.map(([key, p]) => (
            <PipelineCard
              key={key}
              pipelineKey={key}
              pipeline={p}
              onClick={() => setPreviewPipeline({ key, ...p })}
            />
          ))}
          {filteredPipelines.length === 0 && (
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', padding: '8px 4px' }}>
              No pipelines found
            </div>
          )}
        </div>
      )}

      {/* Couplings Section */}
      <SectionHeader
        title="Couplings"
        count={filteredCouplings.length}
        collapsed={collapsed.couplings}
        onToggle={() => toggleSection('couplings')}
        color={theme.colors.accent}
      />
      {!collapsed.couplings && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '4px 0 4px 28px' }}>
            {visibleCouplings.map(([key, c]) => (
              <CouplingChip
                key={key}
                couplingKey={key}
                coupling={c}
                onClick={() => onSelectCoupling(key, c)}
              />
            ))}
          </div>
          {filteredCouplings.length > COUPLING_INITIAL_SHOW && !showAllCouplings && (
            <button
              onClick={() => setShowAllCouplings(true)}
              style={{
                marginTop: 12,
                marginLeft: 28,
                padding: '8px 20px',
                background: 'rgba(99,102,241,0.08)',
                border: '1px solid rgba(99,102,241,0.2)',
                borderRadius: 9999,
                color: theme.colors.accent,
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s ease-out',
              }}
            >
              Show all {filteredCouplings.length} couplings
            </button>
          )}
          {showAllCouplings && filteredCouplings.length > COUPLING_INITIAL_SHOW && (
            <button
              onClick={() => setShowAllCouplings(false)}
              style={{
                marginTop: 12,
                marginLeft: 28,
                padding: '8px 20px',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 9999,
                color: 'rgba(255,255,255,0.5)',
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s ease-out',
              }}
            >
              Show fewer
            </button>
          )}
          {filteredCouplings.length === 0 && (
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', padding: '8px 4px' }}>
              No couplings found
            </div>
          )}
        </div>
      )}

      {/* Sweep action card */}
      <SectionHeader
        title="Sweep"
        count={1}
        collapsed={collapsed.sweep}
        onToggle={() => toggleSection('sweep')}
        color={theme.colors.warning}
      />
      {!collapsed.sweep && (
        <div style={{ marginBottom: 32, padding: '4px 0 4px 28px' }}>
          <SweepCard onClick={onSelectSweep} />
        </div>
      )}

      {/* Results Section */}
      <SectionHeader
        title="Results"
        count=""
        collapsed={collapsed.results}
        onToggle={() => toggleSection('results')}
        color={theme.colors.success}
      />
      {!collapsed.results && (
        <div style={{
          marginBottom: 32,
          marginLeft: 28,
          background: 'rgba(255,255,255,0.025)',
          borderRadius: 12,
          border: '1px solid rgba(255,255,255,0.06)',
          overflow: 'hidden',
          maxHeight: 500,
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        }}>
          <ResultsBrowser
            project={project}
            onSelectResult={onSelectResult}
            selectedResult={null}
            embedded
          />
        </div>
      )}

      {/* Tool Preview Modal */}
      {previewTool && (
        <ToolPreview
          tool={previewTool}
          presets={presets}
          onGo={() => {
            const tool = previewTool;
            setPreviewTool(null);
            onSelectTool(tool);
          }}
          onGoWithPreset={async (preset) => {
            setPreviewTool(null);
            await handlePresetClick(preset);
          }}
          onClose={() => setPreviewTool(null)}
          isMobile={isMobile}
        />
      )}

      {/* Pipeline Preview Modal */}
      {previewPipeline && (
        <PipelinePreview
          pipeline={previewPipeline}
          onGo={() => {
            const p = previewPipeline;
            setPreviewPipeline(null);
            onSelectPipeline(p.key, p);
          }}
          onClose={() => setPreviewPipeline(null)}
          isMobile={isMobile}
        />
      )}
    </div>
  );
}

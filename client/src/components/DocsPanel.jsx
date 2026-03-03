import React, { useState, useEffect, useCallback } from 'react';
import DocsToolList from '../docs/DocsToolList';
import DocsToolPage from '../docs/DocsToolPage';
import DocsCouplingList from '../docs/DocsCouplingList';
import DocsCouplingPage from '../docs/DocsCouplingPage';
import DocsPipelineList from '../docs/DocsPipelineList';
import DocsPipelinePage from '../docs/DocsPipelinePage';
import theme from '../theme.json';

const TABS = [
  { key: 'tools', label: 'Tools' },
  { key: 'couplings', label: 'Couplings' },
  { key: 'pipelines', label: 'Pipelines' },
];

export default function DocsPanel({ isOpen, onClose, initialTab, initialFilter }) {
  const [activeTab, setActiveTab] = useState(initialTab || 'tools');
  const [searchQuery, setSearchQuery] = useState(initialFilter || '');
  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedCoupling, setSelectedCoupling] = useState(null);
  const [selectedPipeline, setSelectedPipeline] = useState(null);

  // Sync with external filter changes
  useEffect(() => {
    if (isOpen && initialTab) setActiveTab(initialTab);
    if (isOpen && initialFilter) {
      setSearchQuery(initialFilter);
      // If the filter matches a specific tool key, open it directly
      if (initialTab === 'tools' && initialFilter) {
        setSelectedTool(initialFilter);
        setSearchQuery('');
      } else if (initialTab === 'pipelines' && initialFilter) {
        setSelectedPipeline(initialFilter);
        setSearchQuery('');
      }
    }
  }, [isOpen, initialTab, initialFilter]);

  // Reset detail view when switching tabs
  const handleTabSwitch = useCallback((tab) => {
    setActiveTab(tab);
    setSelectedTool(null);
    setSelectedCoupling(null);
    setSelectedPipeline(null);
  }, []);

  // Handle navigating from pipeline tool link to tool docs
  const handleOpenToolFromPipeline = useCallback((toolKey) => {
    setActiveTab('tools');
    setSelectedTool(toolKey);
    setSelectedCoupling(null);
    setSelectedPipeline(null);
  }, []);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 998,
        }}
      />

      {/* Panel */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 420,
        height: '100vh',
        background: theme.colors.bgSecondary,
        borderLeft: `1px solid ${theme.colors.border}`,
        zIndex: 999,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.3)',
      }}>
        {/* Header */}
        <div style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${theme.colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: theme.colors.text }}>
            Documentation
          </span>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: theme.colors.textSecondary,
              fontSize: 18,
              cursor: 'pointer',
              padding: '2px 6px',
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Search */}
        <div style={{ padding: '8px 16px', flexShrink: 0 }}>
          <input
            type="text"
            placeholder="Search docs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: theme.colors.bgTertiary,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: 6,
              color: theme.colors.text,
              fontSize: 13,
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: 2,
          padding: '0 16px 8px',
          flexShrink: 0,
        }}>
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => handleTabSwitch(tab.key)}
              style={{
                flex: 1,
                padding: '6px 0',
                background: activeTab === tab.key ? theme.colors.accent : theme.colors.bgTertiary,
                border: 'none',
                borderRadius: 4,
                color: activeTab === tab.key ? '#fff' : theme.colors.textSecondary,
                fontSize: 12,
                fontWeight: activeTab === tab.key ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 16px 16px',
        }}>
          {activeTab === 'tools' && (
            selectedTool ? (
              <DocsToolPage
                toolKey={selectedTool}
                onBack={() => setSelectedTool(null)}
              />
            ) : (
              <DocsToolList
                searchQuery={searchQuery}
                onSelectTool={(key) => setSelectedTool(key)}
              />
            )
          )}

          {activeTab === 'couplings' && (
            selectedCoupling ? (
              <DocsCouplingPage
                couplingKey={selectedCoupling}
                onBack={() => setSelectedCoupling(null)}
              />
            ) : (
              <DocsCouplingList
                searchQuery={searchQuery}
                onSelectCoupling={(key) => setSelectedCoupling(key)}
              />
            )
          )}

          {activeTab === 'pipelines' && (
            selectedPipeline ? (
              <DocsPipelinePage
                pipelineKey={selectedPipeline}
                onBack={() => setSelectedPipeline(null)}
                onOpenToolDocs={handleOpenToolFromPipeline}
              />
            ) : (
              <DocsPipelineList
                searchQuery={searchQuery}
                onSelectPipeline={(key) => setSelectedPipeline(key)}
              />
            )
          )}
        </div>
      </div>
    </>
  );
}

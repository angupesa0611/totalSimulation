import React, { useEffect, useRef, useState } from 'react';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';

/**
 * MolStar PluginContext React wrapper.
 * Manages plugin lifecycle and exposes the plugin instance via ref.
 */
export default function MolStarPlugin({ onPluginReady, style }) {
  const containerRef = useRef(null);
  const pluginRef = useRef(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let plugin = null;
    let disposed = false;

    async function init() {
      if (!containerRef.current || disposed) return;

      try {
        plugin = await createPluginUI({
          target: containerRef.current,
          spec: {
            ...DefaultPluginUISpec(),
            layout: {
              initial: {
                isExpanded: false,
                showControls: false,
                regionState: {
                  left: 'hidden',
                  right: 'hidden',
                  top: 'hidden',
                  bottom: 'hidden',
                },
              },
            },
          },
        });

        if (disposed) {
          plugin.dispose();
          return;
        }

        pluginRef.current = plugin;
        setReady(true);
        if (onPluginReady) onPluginReady(plugin);
      } catch (err) {
        console.error('MolStar init failed:', err);
      }
    }

    init();

    return () => {
      disposed = true;
      if (pluginRef.current) {
        pluginRef.current.dispose();
        pluginRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        ...style,
      }}
    />
  );
}

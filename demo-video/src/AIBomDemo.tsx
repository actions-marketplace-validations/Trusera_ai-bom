import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";

// ─── Color palette ───────────────────────────────────────────────
const BG = "#0d1117";
const TITLE_BAR = "#161b22";
const BORDER = "#30363d";
const TEXT = "#c9d1d9";
const DIM = "#6e7681";
const CYAN = "#58a6ff";
const GREEN = "#3fb950";
const YELLOW = "#d29922";
const RED = "#f85149";
const MAGENTA = "#bc8cff";
const TEAL = "#2dd4bf";

// ─── Typing helpers ──────────────────────────────────────────────
const typeText = (text: string, frame: number, startFrame: number, charsPerFrame = 0.5) => {
  const elapsed = Math.max(0, frame - startFrame);
  const chars = Math.floor(elapsed * charsPerFrame);
  return text.slice(0, Math.min(chars, text.length));
};

const showAfter = (frame: number, threshold: number) => frame >= threshold;

// ─── Cursor blink ────────────────────────────────────────────────
const Cursor: React.FC<{ visible: boolean }> = ({ visible }) => {
  const frame = useCurrentFrame();
  const blink = Math.floor(frame / 8) % 2 === 0;
  if (!visible) return null;
  return (
    <span style={{ color: GREEN, opacity: blink ? 1 : 0 }}>|</span>
  );
};

// ─── Spinner ─────────────────────────────────────────────────────
const spinChars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const Spinner: React.FC<{ color?: string }> = ({ color = CYAN }) => {
  const frame = useCurrentFrame();
  const idx = Math.floor(frame / 3) % spinChars.length;
  return <span style={{ color }}>{spinChars[idx]} </span>;
};

// ─── Terminal chrome ─────────────────────────────────────────────
const TerminalChrome: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      width: 760,
      margin: "0 auto",
      borderRadius: 10,
      overflow: "hidden",
      border: `1px solid ${BORDER}`,
      boxShadow: "0 16px 48px rgba(0,0,0,0.6)",
    }}
  >
    {/* Title bar */}
    <div
      style={{
        background: TITLE_BAR,
        height: 36,
        display: "flex",
        alignItems: "center",
        padding: "0 14px",
        gap: 8,
      }}
    >
      <div style={{ width: 12, height: 12, borderRadius: 6, background: "#ff5f56" }} />
      <div style={{ width: 12, height: 12, borderRadius: 6, background: "#ffbd2e" }} />
      <div style={{ width: 12, height: 12, borderRadius: 6, background: "#27c93f" }} />
      <span
        style={{
          flex: 1,
          textAlign: "center",
          color: DIM,
          fontSize: 12,
          fontFamily: "monospace",
        }}
      >
        ai-bom — bash
      </span>
    </div>
    {/* Terminal body */}
    <div
      style={{
        background: BG,
        padding: "14px 16px",
        minHeight: 420,
        fontFamily: "'SF Mono', 'Fira Code', 'Cascadia Code', monospace",
        fontSize: 13,
        lineHeight: 1.6,
        color: TEXT,
        whiteSpace: "pre-wrap",
      }}
    >
      {children}
    </div>
  </div>
);

// ─── Findings data ───────────────────────────────────────────────
const findings = [
  { name: "OpenAI SDK",            type: "LLM Provider",    risk: 30, sev: "critical", file: "app/llm.py" },
  { name: "Anthropic SDK",         type: "LLM Provider",    risk: 25, sev: "high",     file: "app/claude.py" },
  { name: "gpt-4o",                type: "Model Reference", risk: 15, sev: "medium",   file: "app/llm.py" },
  { name: "LangChain",             type: "Agent Framework", risk: 20, sev: "high",     file: "app/chain.py" },
  { name: "CrewAI",                type: "Agent Framework", risk: 20, sev: "high",     file: "app/agents.py" },
  { name: "Ollama Container",      type: "AI Container",    risk: 10, sev: "medium",   file: "docker-compose.yml" },
  { name: "AI Agent Node",         type: "n8n AI Node",     risk: 30, sev: "critical", file: "workflow.json" },
  { name: "MCP Client",            type: "n8n MCP",         risk: 25, sev: "high",     file: "workflow.json" },
  { name: "Webhook (no auth)",     type: "n8n Trigger",     risk: 25, sev: "high",     file: "workflow.json" },
  { name: "AWS Bedrock",           type: "Cloud AI",        risk: 10, sev: "medium",   file: "infra/main.tf" },
];

const sevColor = (sev: string) => {
  switch (sev) {
    case "critical": return RED;
    case "high":     return YELLOW;
    case "medium":   return CYAN;
    default:         return GREEN;
  }
};

// ─── Main component ──────────────────────────────────────────────
export const AIBomDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Scene 1: Type command (frames 0-60) ──
  const cmd = "ai-bom scan ./my-project";
  const typedCmd = typeText(cmd, frame, 10, 0.7);
  const cmdDone = frame >= 10 + cmd.length / 0.7;

  // ── Scene 2: Banner (frames 60-90) ──
  const bannerVisible = showAfter(frame, 65);
  const bannerOpacity = interpolate(frame, [65, 75], [0, 1], { extrapolateRight: "clamp" });

  // ── Scene 3: Scanner progress (frames 90-150) ──
  const scanners = [
    { label: "Running code scanner...",    start: 90 },
    { label: "Running docker scanner...",  start: 105 },
    { label: "Running network scanner...", start: 115 },
    { label: "Running cloud scanner...",   start: 125 },
    { label: "Running n8n scanner...",     start: 135 },
  ];

  // ── Scene 4: Found count (frames 150-180) ──
  const foundVisible = showAfter(frame, 155);
  const foundOpacity = interpolate(frame, [155, 165], [0, 1], { extrapolateRight: "clamp" });

  // ── Scene 5: Summary panel (frames 180-300) ──
  const summaryVisible = showAfter(frame, 185);
  const summarySlide = interpolate(frame, [185, 210], [20, 0], { extrapolateRight: "clamp" });
  const summaryOpacity = interpolate(frame, [185, 205], [0, 1], { extrapolateRight: "clamp" });

  const summaryData = [
    { label: "LLM Providers",    count: 2, color: MAGENTA },
    { label: "Agent Frameworks",  count: 2, color: CYAN },
    { label: "Model References",  count: 1, color: TEXT },
    { label: "AI Containers",     count: 1, color: TEAL },
    { label: "n8n AI Nodes",      count: 3, color: YELLOW },
    { label: "Cloud AI",          count: 1, color: GREEN },
  ];

  // ── Scene 6: Findings table (frames 300-480) ──
  const tableVisible = showAfter(frame, 300);
  const tableOpacity = interpolate(frame, [300, 315], [0, 1], { extrapolateRight: "clamp" });

  // ── Scene 7: CTA (frames 480-540) ──
  const ctaOpacity = interpolate(frame, [485, 510], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#010409",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <TerminalChrome>
        {/* Prompt + Command */}
        <div>
          <span style={{ color: GREEN }}>$</span>{" "}
          <span style={{ color: TEXT }}>{typedCmd}</span>
          {!cmdDone && <Cursor visible />}
        </div>

        {/* Banner */}
        {bannerVisible && (
          <div style={{ opacity: bannerOpacity, marginTop: 6 }}>
            <span style={{ color: CYAN }}>
              {"━".repeat(52)}
            </span>
            {"\n"}
            <span style={{ color: CYAN, fontWeight: "bold" }}>
              {"  AI-BOM Discovery Scanner"}
            </span>
            <span style={{ color: DIM }}>{" by "}</span>
            <span style={{ color: TEAL, fontWeight: "bold" }}>Trusera</span>
            {"\n"}
            <span style={{ color: CYAN }}>
              {"━".repeat(52)}
            </span>
          </div>
        )}

        {/* Scanner progress lines */}
        {scanners.map((s, i) => {
          if (!showAfter(frame, s.start)) return null;
          const done = showAfter(frame, s.start + 15);
          return (
            <div key={i} style={{ marginTop: i === 0 ? 8 : 0 }}>
              {!done && <Spinner />}
              {done && <span style={{ color: GREEN }}>{"✓ "}</span>}
              <span style={{ color: done ? DIM : TEXT }}>{s.label}</span>
              {done && <span style={{ color: DIM }}> done</span>}
            </div>
          );
        })}

        {/* Found count */}
        {foundVisible && (
          <div style={{ opacity: foundOpacity, marginTop: 8 }}>
            <span style={{ color: GREEN, fontWeight: "bold" }}>
              {"Found 10 AI/LLM component(s)"}
            </span>
          </div>
        )}

        {/* Summary panel */}
        {summaryVisible && (
          <div
            style={{
              opacity: summaryOpacity,
              transform: `translateY(${summarySlide}px)`,
              marginTop: 10,
              padding: "8px 12px",
              background: "#161b22",
              borderRadius: 6,
              border: `1px solid ${BORDER}`,
            }}
          >
            <div style={{ color: CYAN, fontWeight: "bold", marginBottom: 4 }}>
              Component Summary
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 20px" }}>
              {summaryData.map((d, i) => {
                const itemVisible = showAfter(frame, 195 + i * 8);
                if (!itemVisible) return null;
                return (
                  <div key={i} style={{ minWidth: 180 }}>
                    <span style={{ color: d.color }}>{d.label}</span>
                    <span style={{ color: DIM }}>{"  "}</span>
                    <span style={{ color: TEXT, fontWeight: "bold" }}>{d.count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Findings table */}
        {tableVisible && (
          <div style={{ opacity: tableOpacity, marginTop: 10 }}>
            <div style={{ color: CYAN, fontWeight: "bold", marginBottom: 4 }}>
              Top Findings
            </div>
            {/* Header */}
            <div style={{ display: "flex", color: DIM, fontSize: 12, borderBottom: `1px solid ${BORDER}`, paddingBottom: 2 }}>
              <span style={{ width: 200 }}>Component</span>
              <span style={{ width: 140 }}>Type</span>
              <span style={{ width: 60, textAlign: "center" }}>Risk</span>
              <span style={{ width: 70, textAlign: "center" }}>Severity</span>
              <span style={{ flex: 1 }}>Source</span>
            </div>
            {/* Rows */}
            {findings.map((f, i) => {
              const rowStart = 310 + i * 12;
              if (!showAfter(frame, rowStart)) return null;
              const rowOpacity = interpolate(frame, [rowStart, rowStart + 8], [0, 1], {
                extrapolateRight: "clamp",
              });
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    opacity: rowOpacity,
                    fontSize: 12,
                    padding: "1px 0",
                  }}
                >
                  <span style={{ width: 200, color: TEXT }}>{f.name}</span>
                  <span style={{ width: 140, color: DIM }}>{f.type}</span>
                  <span
                    style={{
                      width: 60,
                      textAlign: "center",
                      color: sevColor(f.sev),
                      fontWeight: "bold",
                    }}
                  >
                    {f.risk}
                  </span>
                  <span
                    style={{
                      width: 70,
                      textAlign: "center",
                      color: sevColor(f.sev),
                      textTransform: "uppercase",
                      fontSize: 10,
                      fontWeight: "bold",
                    }}
                  >
                    {f.sev}
                  </span>
                  <span style={{ flex: 1, color: DIM }}>{f.file}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* CTA */}
        {showAfter(frame, 485) && (
          <div
            style={{
              opacity: ctaOpacity,
              marginTop: 12,
              textAlign: "center",
              padding: "6px 0",
            }}
          >
            <span style={{ color: TEAL, fontWeight: "bold" }}>
              pip install ai-bom
            </span>
            <span style={{ color: DIM }}>{"  |  "}</span>
            <span style={{ color: CYAN }}>trusera.dev</span>
          </div>
        )}
      </TerminalChrome>
    </div>
  );
};

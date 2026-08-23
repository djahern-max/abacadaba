import React from "react";
import { AbsoluteFill } from "remotion";
import { theme, WIDTH, HEIGHT } from "./theme";
import type { LessonMeta } from "./slides";

/**
 * The sheet chrome that every slide sits inside.
 *
 * This is the signature element. A drawing border with corner registration
 * ticks and a title block in the lower right, carrying the sheet number, the
 * ASC paragraph under discussion, and the revision. It gives the participant a
 * persistent, glanceable citation without a caption competing with the content,
 * and it tells them where they are in the sequence.
 */

const Tick: React.FC<{ x: number; y: number; rx: number; ry: number }> = ({
  x,
  y,
  rx,
  ry,
}) => (
  <>
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 26 * rx > 0 ? 26 : 26,
        height: 1,
        background: theme.color.hairline,
        transform: `translateX(${rx < 0 ? -26 : 0}px)`,
      }}
    />
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 1,
        height: 26,
        background: theme.color.hairline,
        transform: `translateY(${ry < 0 ? -26 : 0}px)`,
      }}
    />
  </>
);

export const Sheet: React.FC<{
  sheet: string;
  citation: string;
  meta: LessonMeta;
  children: React.ReactNode;
}> = ({ sheet, citation, meta, children }) => {
  const m = theme.margin;

  return (
    <AbsoluteFill style={{ background: theme.color.vellum }}>
      {/* Drawing border */}
      <div
        style={{
          position: "absolute",
          left: m,
          top: m,
          right: m,
          bottom: m,
          border: `1px solid ${theme.color.hairline}`,
        }}
      />

      {/* Corner registration ticks, sitting just outside the border */}
      <Tick x={m} y={m} rx={-1} ry={-1} />
      <Tick x={WIDTH - m} y={m} rx={1} ry={-1} />
      <Tick x={m} y={HEIGHT - m} rx={-1} ry={1} />
      <Tick x={WIDTH - m} y={HEIGHT - m} rx={1} ry={1} />

      {/* Content area, inset from the border */}
      <AbsoluteFill
        style={{
          padding: `${m + 64}px ${m + 72}px ${m + 150}px ${m + 72}px`,
        }}
      >
        {children}
      </AbsoluteFill>

      {/* Title block, lower right, inside the border */}
      <div
        style={{
          position: "absolute",
          right: m,
          bottom: m,
          display: "flex",
          fontFamily: theme.font.mono,
          fontSize: theme.size.titleBlock,
          color: theme.color.slate,
          borderTop: `1px solid ${theme.color.hairline}`,
          borderLeft: `1px solid ${theme.color.hairline}`,
          background: theme.color.vellum,
        }}
      >
        <Cell label="COURSE" value={meta.courseCode} width={240} />
        <Cell label="REFERENCE" value={citation} width={360} />
        <Cell label="REV" value={meta.revision} width={90} />
        <Cell label="SHEET" value={sheet} width={140} emphasis />
      </div>

      {/* Draft watermark. Remove when the course is reviewed and published. */}
      <div
        style={{
          position: "absolute",
          left: m,
          bottom: m,
          padding: "10px 18px",
          borderTop: `1px solid ${theme.color.hairline}`,
          borderRight: `1px solid ${theme.color.hairline}`,
          fontFamily: theme.font.mono,
          fontSize: theme.size.titleBlock,
          letterSpacing: "0.08em",
          color: theme.color.flag,
        }}
      >
        {meta.status}
      </div>
    </AbsoluteFill>
  );
};

const Cell: React.FC<{
  label: string;
  value: string;
  width: number;
  emphasis?: boolean;
}> = ({ label, value, width, emphasis }) => (
  <div
    style={{
      width,
      padding: "10px 18px",
      borderRight: `1px solid ${theme.color.hairline}`,
    }}
  >
    <div
      style={{
        fontSize: 15,
        letterSpacing: "0.14em",
        color: theme.color.hairline,
        marginBottom: 4,
      }}
    >
      {label}
    </div>
    <div
      style={{
        color: emphasis ? theme.color.graphite : theme.color.slate,
        fontWeight: emphasis ? 600 : 400,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {value}
    </div>
  </div>
);

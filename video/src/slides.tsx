import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "./theme";
import { revealAt, isRevealed, springAt } from "./reveal";
import type { Figure } from "./lesson-01";

export type LessonMeta = {
  courseCode: string;
  courseTitle: string;
  lessonTitle: string;
  position: string;        // "Lesson 1 of 5" — course-relative, not the package id
  deliveryMethod: string;  // "Self study", "Group live"
  fieldOfStudy: string;
  revision: string;
  revisionDate: string;
  status: string;
};

type SlideProps = { reveals: number[]; figure?: Figure; meta?: LessonMeta };

/** A row/item without a marker of its own reveals with the last marked one. */
const revealTimeFor = (i: number, reveals: number[]) =>
  reveals[Math.min(i, reveals.length - 1)];

/* ------------------------------------------------------------------ */
/* Shared primitives                                                   */
/* ------------------------------------------------------------------ */

const Eyebrow: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: theme.font.mono,
      fontSize: theme.size.caption,
      letterSpacing: "0.16em",
      color: theme.color.slate,
      marginBottom: 28,
    }}
  >
    {children}
  </div>
);

const Heading: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: theme.font.display,
      fontSize: theme.size.heading,
      fontWeight: 700,
      lineHeight: 1.08,
      letterSpacing: "-0.02em",
      color: theme.color.graphite,
      marginBottom: 44,
    }}
  >
    {children}
  </div>
);

const Panel: React.FC<{
  children: React.ReactNode;
  marked?: boolean;
  style?: React.CSSProperties;
}> = ({ children, marked, style }) => (
  <div
    style={{
      background: marked ? theme.color.flagWash : theme.color.vellumEdge,
      border: `1px solid ${marked ? theme.color.flag : theme.color.hairline}`,
      padding: "26px 30px",
      ...style,
    }}
  >
    {children}
  </div>
);

/* ------------------------------------------------------------------ */
/* S-00  Title                                                         */
/* ------------------------------------------------------------------ */

export const Title: React.FC<SlideProps> = ({ reveals, meta }) => {
  const frame = useCurrentFrame();
  const m = meta!;
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>{m.courseTitle.toUpperCase()}</Eyebrow>
      </div>
      <div
        style={{
          ...revealAt(frame, reveals[1]),
          fontFamily: theme.font.display,
          fontSize: theme.size.display,
          fontWeight: 800,
          lineHeight: 1.04,
          letterSpacing: "-0.03em",
          color: theme.color.graphite,
          maxWidth: 1400,
        }}
      >
        {m.lessonTitle}
      </div>
      <div
        style={{
          ...revealAt(frame, reveals[2]),
          marginTop: 44,
          display: "flex",
          gap: 18,
          alignItems: "center",
          fontFamily: theme.font.mono,
          fontSize: theme.size.caption,
          color: theme.color.slate,
        }}
      >
        <span style={{ width: 60, height: 2, background: theme.color.flag }} />
        <span>
          {[m.position, m.deliveryMethod, m.fieldOfStudy]
            .join("\u00A0·\u00A0")
            .toUpperCase()}
        </span>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-01  The misconception                                             */
/* ------------------------------------------------------------------ */

export const Misconception: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();
  const struck = isRevealed(frame, reveals[1]);

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>WHAT EVERYONE STILL SAYS</Eyebrow>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[0]),
          fontFamily: theme.font.display,
          fontSize: theme.size.display,
          fontWeight: 700,
          letterSpacing: "-0.02em",
          color: theme.color.graphite,
          display: "flex",
          alignItems: "baseline",
          gap: 22,
          flexWrap: "wrap",
        }}
      >
        <span>Percentage of completion</span>
        <span style={{ color: theme.color.slate, fontWeight: 400 }}>is an accounting</span>
        <span style={{ position: "relative", display: "inline-block" }}>
          method
          {/* The strikethrough draws itself across the word */}
          <span
            style={{
              position: "absolute",
              left: -6,
              right: -6,
              top: "52%",
              height: 5,
              background: theme.color.flag,
              transformOrigin: "left center",
              transform: `scaleX(${struck ? springAt(frame, reveals[1]) : 0})`,
            }}
          />
        </span>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[2]),
          marginTop: 64,
          fontFamily: theme.font.body,
          fontSize: theme.size.subhead,
          lineHeight: 1.4,
          color: theme.color.graphite,
          maxWidth: 1250,
        }}
      >
        One method you elected&nbsp;&nbsp;→&nbsp;&nbsp;
        <span style={{ color: theme.color.flag, fontWeight: 700 }}>
          two separate judgments
        </span>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-02  The legacy branch                                             */
/* ------------------------------------------------------------------ */

export const LegacyBranch: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>THE MODEL THAT WAS SUPERSEDED</Eyebrow>
        <Heading>ASC 605-35 asked one question</Heading>
      </div>

      <div style={{ display: "flex", gap: 28, alignItems: "stretch" }}>
        <div style={{ ...revealAt(frame, reveals[1]), flex: 1 }}>
          <Panel>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, color: theme.color.slate, marginBottom: 10 }}>
              IF ESTIMATES WERE DEPENDABLE
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: theme.size.subhead, fontWeight: 700, color: theme.color.graphite }}>
              Percentage of completion
            </div>
          </Panel>
        </div>
        <div style={{ ...revealAt(frame, reveals[2]), flex: 1 }}>
          <Panel>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, color: theme.color.slate, marginBottom: 10 }}>
              IF THEY WERE NOT
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: theme.size.subhead, fontWeight: 700, color: theme.color.graphite }}>
              Completed contract
            </div>
          </Panel>
        </div>
      </div>

      <div style={{ ...revealAt(frame, reveals[3]), marginTop: 46 }}>
        <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, letterSpacing: "0.14em", color: theme.color.slate, marginBottom: 18 }}>
          AND EVERY CONTRACTOR'S BALANCE SHEET CARRIED
        </div>
        <div style={{ display: "flex", gap: 28 }}>
          <Panel style={{ flex: 1 }}>
            <span style={{ fontFamily: theme.font.body, fontSize: theme.size.body, color: theme.color.graphite }}>
              Costs in excess of billings
            </span>
          </Panel>
          <Panel style={{ flex: 1 }}>
            <span style={{ fontFamily: theme.font.body, fontSize: theme.size.body, color: theme.color.graphite }}>
              Billings in excess of costs
            </span>
          </Panel>
        </div>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[4]),
          marginTop: 40,
          fontFamily: theme.font.body,
          fontSize: theme.size.body,
          color: theme.color.flag,
          fontWeight: 600,
        }}
      >
        ASC 606 took it apart — not because it was wrong, because it was separate.
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-03  The five steps                                                */
/* ------------------------------------------------------------------ */

const STEPS = [
  "Identify the contract with the customer",
  "Identify the performance obligations",
  "Determine the transaction price",
  "Allocate the transaction price",
  "Recognize revenue when — or as — the entity satisfies a performance obligation",
];

export const FiveSteps: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div>
        <Eyebrow>ONE FRAMEWORK FOR EVERY INDUSTRY</Eyebrow>
        <Heading>Five steps</Heading>
      </div>

      {STEPS.map((step, i) => {
        const last = i === STEPS.length - 1;
        return (
          <div
            key={i}
            style={{
              ...revealAt(frame, reveals[i]),
              display: "flex",
              alignItems: "baseline",
              gap: 30,
              padding: "18px 0",
              borderTop: `1px solid ${theme.color.hairline}`,
            }}
          >
            <span
              style={{
                fontFamily: theme.font.mono,
                fontSize: theme.size.caption,
                color: last ? theme.color.flag : theme.color.slate,
                width: 40,
              }}
            >
              {String(i + 1).padStart(2, "0")}
            </span>
            <span
              style={{
                fontFamily: theme.font.body,
                fontSize: theme.size.body,
                color: theme.color.graphite,
                fontWeight: last ? 700 : 400,
              }}
            >
              {step}
            </span>
          </div>
        );
      })}

      <div
        style={{
          ...revealAt(frame, reveals[5]),
          marginTop: 42,
          display: "flex",
          alignItems: "center",
          gap: 20,
        }}
      >
        <span style={{ width: 60, height: 2, background: theme.color.flag }} />
        <span
          style={{
            fontFamily: theme.font.display,
            fontSize: theme.size.subhead,
            fontWeight: 700,
            color: theme.color.flag,
          }}
        >
          when — or as
        </span>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-04  The fork                                                      */
/* ------------------------------------------------------------------ */

export const Fork: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>STEP 5</Eyebrow>
        <Heading>Not a choice. A test.</Heading>
      </div>

      <div style={{ display: "flex", gap: 32 }}>
        <div style={{ ...revealAt(frame, reveals[1]), flex: 1 }}>
          <Panel style={{ height: "100%" }}>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, letterSpacing: "0.14em", color: theme.color.slate, marginBottom: 14 }}>
              DEFAULT
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: theme.size.subhead, fontWeight: 700, color: theme.color.graphite }}>
              At a point in time
            </div>
          </Panel>
        </div>
        <div style={{ ...revealAt(frame, reveals[2]), flex: 1 }}>
          <Panel marked style={{ height: "100%" }}>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, letterSpacing: "0.14em", color: theme.color.flag, marginBottom: 14 }}>
              MUST QUALIFY
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: theme.size.subhead, fontWeight: 700, color: theme.color.graphite }}>
              Over time
            </div>
          </Panel>
        </div>
      </div>

      <div style={{ ...revealAt(frame, reveals[3]), marginTop: 48 }}>
        <div style={{ fontFamily: theme.font.body, fontSize: theme.size.body, lineHeight: 1.5, color: theme.color.graphite, maxWidth: 1300 }}>
          You do not elect over-time recognition. You test the performance
          obligation against the criteria, and the criteria decide.
        </div>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[4]),
          marginTop: 32,
          fontFamily: theme.font.mono,
          fontSize: theme.size.caption,
          color: theme.color.slate,
        }}
      >
        MEET ANY ONE OF THREE &nbsp;→&nbsp; OVER TIME &nbsp;&nbsp;|&nbsp;&nbsp; FAIL ALL THREE &nbsp;→&nbsp; POINT IN TIME
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-05  The three criteria, and the AND gate                          */
/* ------------------------------------------------------------------ */

const CRITERIA = [
  {
    key: "(a)",
    text: "The customer simultaneously receives and consumes the benefits as the entity performs",
    note: "Rarely construction — nobody consumes a half-built bridge",
  },
  {
    key: "(b)",
    text: "Performance creates or enhances an asset the customer controls as it is created",
    note: "Often fits building on the owner's own land",
  },
  {
    key: "(c)",
    text: "No alternative use, and an enforceable right to payment for performance completed to date",
    note: "Where most construction contracts land",
  },
];

export const Criteria: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();
  const gateOpen = isRevealed(frame, reveals[3]);
  const gate = gateOpen ? springAt(frame, reveals[3]) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div>
        <Eyebrow>ASC 606-10-25-27 &nbsp;·&nbsp; MEET ANY ONE</Eyebrow>
      </div>

      {CRITERIA.map((c, i) => {
        const marked = i === 2 && isRevealed(frame, reveals[2]);
        return (
          <div key={c.key} style={{ ...revealAt(frame, reveals[i]), marginBottom: 18 }}>
            <Panel marked={marked}>
              <div style={{ display: "flex", gap: 26, alignItems: "flex-start" }}>
                <span
                  style={{
                    fontFamily: theme.font.mono,
                    fontSize: theme.size.body,
                    color: marked ? theme.color.flag : theme.color.slate,
                    fontWeight: 600,
                  }}
                >
                  {c.key}
                </span>
                <div>
                  <div style={{ fontFamily: theme.font.body, fontSize: 34, lineHeight: 1.35, color: theme.color.graphite }}>
                    {c.text}
                  </div>
                  <div style={{ fontFamily: theme.font.mono, fontSize: 20, color: theme.color.slate, marginTop: 10 }}>
                    {c.note}
                  </div>
                </div>
              </div>
            </Panel>
          </div>
        );
      })}

      {/* The AND gate. The one animated moment in the lesson, because it is the
          one idea that a static slide genuinely cannot carry: both halves of
          criterion (c) must hold, and practitioners routinely apply only one. */}
      <div
        style={{
          ...revealAt(frame, reveals[3]),
          marginTop: 24,
          display: "flex",
          alignItems: "center",
          gap: 22,
        }}
      >
        <Panel marked style={{ flex: 1, textAlign: "center" }}>
          <span style={{ fontFamily: theme.font.body, fontSize: 30, color: theme.color.graphite }}>
            No alternative use
          </span>
        </Panel>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 38,
            fontWeight: 800,
            color: theme.color.flag,
            transform: `scale(${0.6 + gate * 0.4})`,
            opacity: gate,
          }}
        >
          AND
        </div>
        <Panel marked style={{ flex: 1, textAlign: "center" }}>
          <span style={{ fontFamily: theme.font.body, fontSize: 30, color: theme.color.graphite }}>
            Enforceable right to payment
          </span>
        </Panel>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[4]),
          marginTop: 26,
          fontFamily: theme.font.mono,
          fontSize: theme.size.caption,
          color: theme.color.slate,
          textAlign: "center",
        }}
      >
        COST RECOVERY ALONE IS NOT AN ENFORCEABLE RIGHT TO PAYMENT
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-06  Input and output methods                                      */
/* ------------------------------------------------------------------ */

export const Methods: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();
  const marked = isRevealed(frame, reveals[3]);

  const col = (
    label: string,
    subtitle: string,
    items: string[],
    highlight: number | null,
    revealIndex: number
  ) => (
    <div style={{ ...revealAt(frame, reveals[revealIndex]), flex: 1 }}>
      <div
        style={{
          fontFamily: theme.font.mono,
          fontSize: theme.size.caption,
          letterSpacing: "0.14em",
          color: theme.color.slate,
          paddingBottom: 14,
          borderBottom: `2px solid ${theme.color.graphite}`,
        }}
      >
        {label}
      </div>
      <div style={{ fontFamily: theme.font.body, fontSize: 26, color: theme.color.slate, margin: "16px 0 22px" }}>
        {subtitle}
      </div>
      {items.map((item, i) => {
        const isHit = highlight === i && marked;
        return (
          <div
            key={item}
            style={{
              fontFamily: theme.font.body,
              fontSize: 32,
              padding: "16px 18px",
              marginBottom: 8,
              color: isHit ? theme.color.graphite : theme.color.slate,
              fontWeight: isHit ? 700 : 400,
              background: isHit ? theme.color.flagWash : "transparent",
              border: `1px solid ${isHit ? theme.color.flag : "transparent"}`,
            }}
          >
            {item}
          </div>
        );
      })}
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>A SECOND, SEPARATE DECISION</Eyebrow>
        <Heading>Measuring progress</Heading>
      </div>

      <div style={{ display: "flex", gap: 60 }}>
        {col("INPUT METHODS", "Measure the entity's efforts", ["Costs incurred", "Labor hours", "Machine hours"], 0, 1)}
        {col("OUTPUT METHODS", "Measure results delivered", ["Units delivered", "Milestones reached", "Surveys of performance"], null, 2)}
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[4]),
          marginTop: 46,
          fontFamily: theme.font.body,
          fontSize: theme.size.body,
          lineHeight: 1.45,
          color: theme.color.graphite,
          maxWidth: 1350,
        }}
      >
        Same spreadsheet, often. But you are no longer applying a method you
        elected — you are selecting a measure that must faithfully depict the
        transfer of control.
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* S-07  Summary                                                       */
/* ------------------------------------------------------------------ */

export const Summary: React.FC<SlideProps> = ({ reveals }) => {
  const frame = useCurrentFrame();

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={revealAt(frame, reveals[0])}>
        <Eyebrow>WHAT TO CARRY FORWARD</Eyebrow>
      </div>

      <div style={{ display: "flex", gap: 32, marginBottom: 46 }}>
        <div style={{ ...revealAt(frame, reveals[0]), flex: 1 }}>
          <Panel marked>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, color: theme.color.flag, marginBottom: 14 }}>
              JUDGMENT 01
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: 40, fontWeight: 700, lineHeight: 1.15, color: theme.color.graphite }}>
              Does it qualify for over-time recognition?
            </div>
            <div style={{ fontFamily: theme.font.mono, fontSize: 20, color: theme.color.slate, marginTop: 14 }}>
              ASC 606-10-25-27
            </div>
          </Panel>
        </div>
        <div style={{ ...revealAt(frame, reveals[1]), flex: 1 }}>
          <Panel marked>
            <div style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, color: theme.color.flag, marginBottom: 14 }}>
              JUDGMENT 02
            </div>
            <div style={{ fontFamily: theme.font.display, fontSize: 40, fontWeight: 700, lineHeight: 1.15, color: theme.color.graphite }}>
              Which measure depicts progress faithfully?
            </div>
            <div style={{ fontFamily: theme.font.mono, fontSize: 20, color: theme.color.slate, marginTop: 14 }}>
              ASC 606-10-55-16
            </div>
          </Panel>
        </div>
      </div>

      <div
        style={{
          ...revealAt(frame, reveals[2]),
          borderTop: `1px solid ${theme.color.hairline}`,
          paddingTop: 34,
          fontFamily: theme.font.body,
          fontSize: theme.size.body,
          color: theme.color.slate,
        }}
      >
        <span style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, letterSpacing: "0.14em", marginRight: 20 }}>
          NEXT
        </span>
        What exactly is the performance obligation in a construction contract?
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Generic, data-driven slides                                         */
/* ------------------------------------------------------------------ */

const EMPHASIS_COLOR = {
  right: theme.color.flag,
  wrong: theme.color.slate,
} as const;

export const Statement: React.FC<SlideProps> = ({ reveals, figure }) => {
  const frame = useCurrentFrame();
  if (!figure || figure.kind !== "statement") return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      {figure.lines.map((line, i) => (
        <div
          key={i}
          style={{
            ...revealAt(frame, revealTimeFor(i, reveals)),
            fontFamily: theme.font.display,
            fontSize: theme.size.display,
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: "-0.02em",
            color: theme.color.graphite,
            marginBottom: 16,
          }}
        >
          {line}
        </div>
      ))}
    </div>
  );
};

export const Facts: React.FC<SlideProps> = ({ reveals, figure }) => {
  const frame = useCurrentFrame();
  if (!figure || figure.kind !== "facts") return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      {figure.rows.map((row, i) => (
        <div
          key={row.label}
          style={{
            ...revealAt(frame, revealTimeFor(i, reveals)),
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
            gap: 40,
            padding: "22px 0",
            borderTop: `1px solid ${theme.color.hairline}`,
          }}
        >
          <span style={{ fontFamily: theme.font.body, fontSize: theme.size.body, color: theme.color.slate }}>
            {row.label}
          </span>
          <span
            style={{
              fontFamily: theme.font.mono,
              fontSize: theme.size.subhead,
              fontWeight: 600,
              color: theme.color.graphite,
            }}
          >
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/**
 * Right-aligned figure column, left-aligned labels, monospace for the
 * numbers so digits line up. `emphasis: "wrong"` renders in slate, not red —
 * this is a working calculation, not an error state.
 */
export const Calc: React.FC<SlideProps> = ({ reveals, figure }) => {
  const frame = useCurrentFrame();
  if (!figure || figure.kind !== "calc") return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      {figure.rows.map((row, i) => (
        <div
          key={row.label}
          style={{
            ...revealAt(frame, revealTimeFor(i, reveals)),
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
            gap: 40,
            padding: "14px 0",
            borderTop: row.rule ? `1px solid ${theme.color.hairline}` : "1px solid transparent",
          }}
        >
          <span style={{ fontFamily: theme.font.body, fontSize: theme.size.body, color: theme.color.slate }}>
            {row.label}
          </span>
          <span
            style={{
              fontFamily: theme.font.mono,
              fontSize: theme.size.subhead,
              fontWeight: 600,
              textAlign: "right",
              color: row.emphasis ? EMPHASIS_COLOR[row.emphasis] : theme.color.graphite,
            }}
          >
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
};

export const List: React.FC<SlideProps> = ({ reveals, figure }) => {
  const frame = useCurrentFrame();
  if (!figure || figure.kind !== "list") return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      {figure.items.map((item, i) => (
        <div
          key={item}
          style={{
            ...revealAt(frame, revealTimeFor(i, reveals)),
            display: "flex",
            alignItems: "baseline",
            gap: 30,
            padding: "18px 0",
            borderTop: `1px solid ${theme.color.hairline}`,
          }}
        >
          <span style={{ fontFamily: theme.font.mono, fontSize: theme.size.caption, color: theme.color.slate, width: 40 }}>
            {String(i + 1).padStart(2, "0")}
          </span>
          <span style={{ fontFamily: theme.font.body, fontSize: theme.size.body, color: theme.color.graphite }}>
            {item}
          </span>
        </div>
      ))}
    </div>
  );
};

export const Compare: React.FC<SlideProps> = ({ reveals, figure }) => {
  const frame = useCurrentFrame();
  if (!figure || figure.kind !== "compare") return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", height: "100%" }}>
      <div style={{ display: "flex", gap: 32 }}>
        {figure.columns.map((col, i) => (
          <div key={col.heading} style={{ ...revealAt(frame, revealTimeFor(i, reveals)), flex: 1 }}>
            <Panel marked={col.emphasis === "right"} style={{ height: "100%" }}>
              <div
                style={{
                  fontFamily: theme.font.mono,
                  fontSize: theme.size.caption,
                  letterSpacing: "0.14em",
                  marginBottom: 20,
                  color: col.emphasis ? EMPHASIS_COLOR[col.emphasis] : theme.color.slate,
                }}
              >
                {col.heading.toUpperCase()}
              </div>
              {col.rows.map((row) => (
                <div
                  key={row.label}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "12px 0",
                    borderTop: `1px solid ${theme.color.hairline}`,
                  }}
                >
                  <span style={{ fontFamily: theme.font.body, fontSize: 26, color: theme.color.slate }}>
                    {row.label}
                  </span>
                  <span
                    style={{
                      fontFamily: theme.font.mono,
                      fontSize: 30,
                      fontWeight: 600,
                      color: col.emphasis ? EMPHASIS_COLOR[col.emphasis] : theme.color.graphite,
                    }}
                  >
                    {row.value}
                  </span>
                </div>
              ))}
            </Panel>
          </div>
        ))}
      </div>
    </div>
  );
};

export const SLIDES = {
  Title,
  Misconception,
  LegacyBranch,
  FiveSteps,
  Fork,
  Criteria,
  Methods,
  Summary,
  Statement,
  Facts,
  Calc,
  List,
  Compare,
} as const;

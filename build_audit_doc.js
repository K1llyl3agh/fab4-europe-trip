const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  BorderStyle, WidthType, AlignmentType, ShadingType, HeadingLevel,
  Header, Footer, PageNumber, ImageRun, VerticalAlign, PageBreak
} = require('docx');

const NAVY = '1F3864';
const BLUE = '2E74B5';
const RED = 'C00000';
const GREEN = '2E7D32';
const AMBER = 'B98A30';
const GREY = '595959';
const INK = '262626';

// No. | Date/Area | Item & action needed | Priority
const COLS = [560, 1760, 5400, 1320];
const COLS_SUM = COLS.reduce((a, b) => a + b, 0);

function cell(text, opts = {}) {
  const { bold = false, color = INK, size = 18, shade = null, width, align = AlignmentType.LEFT, italics = false } = opts;
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    shading: shade ? { type: ShadingType.CLEAR, color: 'auto', fill: shade } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: (Array.isArray(text) ? text : [text]).map(t =>
      typeof t === 'string'
        ? new Paragraph({ alignment: align, children: [new TextRun({ text: t, bold, color, size, italics, font: 'Source Sans Pro' })] })
        : t
    ),
  });
}

function headerRow(labels, cols) {
  return new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: labels.map((l, i) => cell(l, { bold: true, color: 'FFFFFF', size: 18, shade: NAVY, width: cols[i] })),
  });
}

function priorityCell(kind, width) {
  const label = kind === 'gap' ? 'NEEDS BOOKING' : kind === 'decide' ? 'NEEDS DECISION' : 'WORTH CHECKING';
  const color = kind === 'gap' ? RED : kind === 'decide' ? RED : AMBER;
  return cell(label, { bold: true, color, size: 16, width, align: AlignmentType.CENTER });
}

function row(num, dateArea, itemHtml, kind) {
  return new TableRow({
    cantSplit: true,
    children: [
      cell(String(num), { width: COLS[0], bold: true, size: 18, color: NAVY, align: AlignmentType.CENTER }),
      cell(dateArea, { width: COLS[1], bold: true, size: 17, color: NAVY }),
      cell(itemHtml, { width: COLS[2], size: 17 }),
      priorityCell(kind, COLS[3]),
    ],
  });
}

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 320, after: 120 },
    border: { bottom: { color: NAVY, space: 4, style: BorderStyle.SINGLE, size: 8 } },
    children: [new TextRun({ text, bold: true, color: BLUE, size: 24, font: 'Source Sans Pro' })],
  });
}

function lede(text) {
  return new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({ text, italics: true, color: GREY, size: 18, font: 'Source Sans Pro' })],
  });
}

function table(rows, labels, cols, colsSum) {
  return new Table({
    width: { size: colsSum, type: WidthType.DXA },
    columnWidths: cols,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
      left: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
      right: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
      insideVertical: { style: BorderStyle.SINGLE, size: 4, color: 'D9D9D9' },
    },
    rows: [headerRow(labels, cols), ...rows],
  });
}

// ---------- CONTENT: single whole-document numbered punch list ----------
// Everything already booked/confirmed/fixed has been removed. Only genuinely
// outstanding items remain, numbered in trip order. Re-checked against all
// changes made today: Tower of London Tour + River Tour now confirmed
// (Headout booking #33605663 / #33605662, tickets on Gary's app) so that
// item has been removed from this list; the Fiumicino (FCO) transfer was
// re-checked against the current 32-page Travel Documents PDF (20 Aug 2026
// version) and its wording corrected below.

const items = [
  { num: 20, dateArea: 'Wed 23 Sep\nMilan / Venice', item: 'Dinner in Milan (7:00pm, all three day-route Options A/B/C) still needs a restaurant picked from Cantine Milano, L\'Immagine Bistrot or Casa Festa Alcolica. If Option C (Venice Lunch) is the one taken, the 12:30pm Venice lunch spot also still needs choosing – no shortlist attached yet.', kind: 'gap' },
  { num: 21, dateArea: 'Thu 10 Sep\nOutbound', item: 'Singapore connection (~2 hr, Qantas → British Airways) – confirm checked baggage goes through to Rome across the airline change.', kind: 'warn' },
  { num: 22, dateArea: 'Fri 11 Sep\nOutbound', item: 'Heathrow connection (~85 min) – clears BA’s 75-minute T5 minimum connection time, but only by about 10 minutes. No action possible, just worth knowing there’s no margin if the overnight sector runs late.', kind: 'warn' },
  { num: 23, dateArea: 'Ongoing', item: 'International Driving Permit (IDP) – Gary’s is confirmed (IDP196978); Karen, Deb and Tom are not yet ticked on the site\'s IDP checklist.', kind: 'warn' },
];

// ---------- Recent changes (last updates made to the site) ----------
const recentChanges = [
  { date: '30/08/2026', time: '10:15am', text: 'Fixed a stale Things To Do entry for the Hard Rock Cafe dinner (26 Sept) that still showed "To Book" even though the day schedule already had it confirmed (OpenTable confirmation #496211) – now shows Booked in both places.' },
  { date: '30/08/2026', time: '10:15am', text: 'Emailed the Meliá White House about arranging the Heathrow transfer for 27 Sept (see item 19 below); corrected an email drafting error that had given Tom the surname "Gyde" instead of his correct surname, Akhurst.' },
  { date: '30/08/2026', time: '10:15am', text: 'Removed the Things to Take, UK ETA Applications and Passport Validity Check tick-lists from the site now that packing, ETAs and passport checks are all done.' },
  { date: '30/08/2026', time: '10:15am', text: 'Full re-audit run: flagged a genuine scheduling conflict on 24 Sept ("Tapas and Gin for Deb" no longer fit the day) and the still-open Milan dinner / Venice lunch restaurant choices.' },
  { date: '30/08/2026', time: '10:45am', text: '"Tapas and Gin for Deb" (24 Sept) dropped from the schedule per Gary\'s decision – resolved and removed from this list.' },
  { date: '31/08/2026', time: '9:07pm', text: 'The Lighterman (24 Sept) dinner time change to 7:30pm CONFIRMED by Teagan, Reservations – booking 4NJL3Z4M6XN3 amended to 19:30–21:30 for 4 guests. The red "TO BE CONFIRMED" warning has been replaced with a green confirmed note on the day card, and the day-24 route map updated to match.' },
  { date: '31/08/2026', time: '8:20pm', text: 'Added the Queen Victoria cruise booking summary (booking reference 3Q8W5T, ship, voyage V618D, departure 14/09/2026) to the top of the Cruise section, ahead of the Gala Evenings / Onboard Costs / Booked Tours boxes.' },
  { date: '31/08/2026', time: '8:20pm', text: 'Added "Boarding Pass - G&K" and "Luggage Tags - G&K" to the Travel Documents section, each with its own QR code linking to the PDF.' },
  { date: '31/08/2026', time: '9:35pm', text: 'Fixed a bug in push_fab4_live.command where a single locked file could silently halt the entire live push part-way through with no commit or deploy reaching GitHub/Netlify; it now clears stale files first and skips-and-warns instead of aborting.' },
  { date: '01/09/2026', time: '8:18pm', text: 'Meliá White House → Heathrow transfer (item 19) CONFIRMED – the concierge (Rowan Armitt-Brewster) confirmed 6:00pm hotel departure for the 10:00pm BA15 flight, private Mercedes with chauffeur, £135. Removed from Things to Do and Things to Consider – London (both still showed the old 7:00pm/"To Confirm" placeholder); the 27 Sept day card now shows a confirmed transfer box instead. Still need to reply with the lead passenger\'s contact number to finalise the booking.' },
];

const gapCount = items.filter(i => i.kind === 'gap').length;
const decideCount = items.filter(i => i.kind === 'decide').length;
const warnCount = items.filter(i => i.kind === 'warn').length;

const children = [];

children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 40 },
  children: [new TextRun({ text: 'FAB4 Does Europe', bold: true, color: NAVY, size: 56, font: 'Prototype' })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 300 },
  children: [new TextRun({ text: 'Audit – Outstanding Items – September 2026', bold: true, color: BLUE, size: 28, font: 'Source Sans Pro' })],
}));

children.push(new Paragraph({
  spacing: { after: 140 },
  children: [new TextRun({
    text: 'This document lists everything still outstanding across the whole trip (10–29 September 2026) – every flight, transfer, hire car, hotel and booking that’s already confirmed has been checked and removed from this list. What remains below is a numbered punch-list: items marked NEEDS BOOKING require a confirmation or booking action, NEEDS DECISION means the plan itself needs a call from Gary/Karen (nothing to book yet), and WORTH CHECKING are tight connections or verification steps worth a final look before departure, but need no new booking.',
    color: INK, size: 19, font: 'Source Sans Pro',
  })],
}));

children.push(new Paragraph({
  spacing: { after: 260 },
  children: [new TextRun({
    text: `Re-audit run today (1 Sept 2026): The Meliá White House → Heathrow transfer (item 19) is now CONFIRMED – the hotel's concierge confirmed 6:00pm hotel departure for the 10:00pm BA15 flight (private Mercedes, £135) – and no longer appears on this outstanding list; a small follow-up (sending the lead passenger's contact number) remains, noted under Recent changes. The Lighterman dinner time change (24 Sept) is also CONFIRMED (booking 4NJL3Z4M6XN3, 19:30–21:30). Item numbering on this list continues from where each audit left off rather than resetting to 1, so a number always refers to the same underlying issue across revisions – hence the list below starts at 20. ${gapCount} item${gapCount === 1 ? '' : 's'} need booking${decideCount ? `, ${decideCount} need${decideCount === 1 ? 's' : ''} a decision` : ''}, and ${warnCount} ${warnCount === 1 ? 'is' : 'are'} worth a final check.`,
    italics: true, color: GREY, size: 18, font: 'Source Sans Pro',
  })],
}));

children.push(sectionHeading('Recent changes'));
recentChanges.forEach((c, i) => {
  children.push(new Paragraph({
    spacing: { after: 100 },
    children: [
      new TextRun({ text: `${i + 1}. `, bold: true, color: NAVY, size: 18, font: 'Source Sans Pro' }),
      new TextRun({ text: `${c.date}, ${c.time} - `, bold: true, color: NAVY, size: 18, font: 'Source Sans Pro' }),
      new TextRun({ text: c.text, color: INK, size: 18, font: 'Source Sans Pro' }),
    ],
  }));
});

children.push(sectionHeading('Outstanding items'));
children.push(table(
  items.map(i => row(i.num, i.dateArea, i.item, i.kind)),
  ['#', 'Date / Area', 'Item & action needed', 'Priority'],
  COLS, COLS_SUM
));

children.push(new Paragraph({
  spacing: { before: 280 },
  children: [new TextRun({
    text: 'Everything else – all flights, the cruise booking (Deck 8, cabins 8118 & 8112, booking CNZ-83509), the hire car, every hotel’s address/phone/dates/booking references, the Vatican and Colosseum tours, Six the Musical, and all Sydney/Wellington domestic connections – is booked, confirmed, and matches the official Travel Documents (see Flight Summary, Hotel Directory and Travel Documents on the website for full reference numbers).',
    italics: true, color: GREY, size: 18, font: 'Source Sans Pro',
  })],
}));

// ---------- FOOTER ----------
const today = new Date();
const dd = String(today.getDate()).padStart(2, '0');
const mm = String(today.getMonth() + 1).padStart(2, '0');
const yyyy = today.getFullYear();

const footerTable = new Table({
  width: { size: 10040, type: WidthType.DXA },
  columnWidths: [4500, 2240, 3300],
  alignment: AlignmentType.CENTER,
  borders: {
    top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    bottom: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    insideHorizontal: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    insideVertical: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  },
  rows: [new TableRow({
    children: [
      new TableCell({
        width: { size: 4500, type: WidthType.DXA },
        children: [new Paragraph({
          children: [
            new TextRun({ text: 'Page ', size: 12, color: GREY, font: 'Source Sans Pro' }),
            new TextRun({ children: [PageNumber.CURRENT], size: 12, color: GREY, font: 'Source Sans Pro' }),
            new TextRun({ text: ' of ', size: 12, color: GREY, font: 'Source Sans Pro' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 12, color: GREY, font: 'Source Sans Pro' }),
            new TextRun({ text: `   |   Printed: ${dd}/${mm}/${yyyy} (Version 3.8)`, size: 12, color: GREY, font: 'Source Sans Pro' }),
          ],
        })],
      }),
      new TableCell({ width: { size: 2240, type: WidthType.DXA }, children: [new Paragraph('')] }),
      new TableCell({
        width: { size: 3300, type: WidthType.DXA },
        children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'FAB4 Europe Trip – Audit', size: 12, color: GREY, font: 'Source Sans Pro' })] })],
      }),
    ],
  })],
});

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1000, right: 1100, bottom: 700, left: 1100, header: 708, footer: 708 },
      },
    },
    footers: { default: new Footer({ children: [footerTable] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('Fab4_Audit_v3.8.docx', buf);
  console.log('Wrote Fab4_Audit_v3.8.docx', buf.length, 'bytes');
});

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
  const label = kind === 'gap' ? 'NEEDS BOOKING' : 'WORTH CHECKING';
  const color = kind === 'gap' ? RED : AMBER;
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
// changes made today: Vatican/Colosseum tours confirmed with vouchers+QR,
// Civitavecchia transfer confirmed 12pm, Travel Docs replaced with the
// 21 Aug version, Travel Cover PDF added, Villefranche tender-port note
// added, Deb & Tom's To-Do page added (with their own IDP checklist), and
// the Infinity Holidays after-hours line added to Emergency Contacts.

const items = [
  { num: 1, dateArea: 'Fri 11 Sep\nRome arrival', item: 'Fiumicino (FCO) → The Republic Hotel transfer – no booking reference on file, and it doesn’t appear in the confirmed 23-page itinerary at all (only in the original 14 Jan quote). Confirm with Lynaire.', kind: 'gap' },
  { num: 2, dateArea: 'Sat 26 Sep\nLondon', item: 'Tower of London + Crown Jewels + River Tour combo – still not confirmed by Jennifer at Headout (jennifer@inspire.headout.com). Checked the mailbox again – only an earlier guidance thread found, no booking confirmation on file.', kind: 'gap' },
  { num: 3, dateArea: 'Sun 27 Sep\nLondon departure', item: 'Meliá White House → Heathrow (T5) transfer – NOT CONFIRMED. No transfer mode booked for the 7:00pm hotel departure ahead of the 10:00pm BA15.', kind: 'gap' },
  { num: 4, dateArea: 'Thu 10 Sep\nOutbound', item: 'Singapore connection (~2 hr, Qantas → British Airways) – confirm checked baggage goes through to Rome across the airline change.', kind: 'warn' },
  { num: 5, dateArea: 'Fri 11 Sep\nOutbound', item: 'Heathrow connection (~85 min) – clears BA’s 75-minute T5 minimum connection time, but only by about 10 minutes. No action possible, just worth knowing there’s no margin if the overnight sector runs late.', kind: 'warn' },
  { num: 6, dateArea: 'Mon 21–24 Sep\nHire car', item: 'Avis Mercedes Vito is a manual transmission (changed from the automatic Ford Kuga SUV in the original quote, ref NZ759149602) – confirm whoever’s driving in Italy is comfortable with a manual gearbox.', kind: 'warn' },
  { num: 7, dateArea: 'Thu 24 Sep\nMilan → London', item: 'With the corrected BA575/transfer timing, hotel arrival is now ~6:00pm – only ~30 min before the 6:30pm Lighterman dinner booking. Decide whether to skip pre-dinner drinks or move the dinner booking.', kind: 'warn' },
  { num: 8, dateArea: 'Ongoing', item: 'UK Electronic Travel Authorisation (ETA) – verify all 4 travellers’ applications are approved via the checklist on the website.', kind: 'warn' },
  { num: 9, dateArea: 'Ongoing', item: 'Passport validity – verify all 4 passports are valid to at least 29 Mar 2027 (6 months beyond the 29 Sep 2026 return) via the checklist on the website.', kind: 'warn' },
  { num: 10, dateArea: 'Ongoing', item: 'International Driving Permit (IDP) – Gary’s is confirmed (IDP196978); Karen, Deb and Tom are not yet ticked. Deb & Tom now have their own IDP checklist on the new Deb & Tom’s To-Do page – still needs to be filled in.', kind: 'warn' },
];

const gapCount = items.filter(i => i.kind === 'gap').length;
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
    text: 'This document lists everything still outstanding across the whole trip (10–29 September 2026) – every flight, transfer, hire car, hotel and booking that’s already confirmed has been checked and removed from this list. What remains below is a numbered punch-list: items marked NEEDS BOOKING require a confirmation or booking action; items marked WORTH CHECKING are tight connections or verification steps worth a final look before departure, but need no new booking.',
    color: INK, size: 19, font: 'Source Sans Pro',
  })],
}));

children.push(new Paragraph({
  spacing: { after: 260 },
  children: [new TextRun({
    text: `Re-checked today against: Vatican & Colosseum tours (now confirmed, with vouchers and QR codes on the day cards), the Civitavecchia transfer (12pm pickup confirmed), the replaced Travel Documents PDF (21 Aug 2026 version), the new Travel Cover summary PDF, the Villefranche tender-port note, the new Deb & Tom’s To-Do page, and the Infinity Holidays after-hours line (now added to Emergency Contacts). ${gapCount} item${gapCount === 1 ? '' : 's'} need booking, ${warnCount} ${warnCount === 1 ? 'is' : 'are'} worth a final check.`,
    italics: true, color: GREY, size: 18, font: 'Source Sans Pro',
  })],
}));

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
            new TextRun({ text: `   |   Printed: ${dd}/${mm}/${yyyy} (Version 3.0)`, size: 12, color: GREY, font: 'Source Sans Pro' }),
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
  fs.writeFileSync('Fab4_Audit_v3.0.docx', buf);
  console.log('Wrote Fab4_Audit_v3.0.docx', buf.length, 'bytes');
});

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

const COLS = [1600, 2000, 3900, 1540]; // Date | Connection | Details | Status
const COLS_SUM = COLS.reduce((a,b)=>a+b,0);

const VCOLS = [1900, 3200, 3200, 1740]; // Item | Site currently shows | Official document shows | Status/Action
const VCOLS_SUM = VCOLS.reduce((a,b)=>a+b,0);

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

function statusCell(label, kind, width) {
  const color = kind === 'gap' ? RED : kind === 'warn' ? AMBER : GREEN;
  return cell(label, { bold: true, color, size: 17, width });
}

function row(date, connection, details, statusLabel, statusKind) {
  return new TableRow({
    cantSplit: true,
    children: [
      cell(date, { width: COLS[0], bold: true, size: 18, color: NAVY }),
      cell(connection, { width: COLS[1], bold: true, size: 18 }),
      cell(details, { width: COLS[2], size: 17 }),
      statusCell(statusLabel, statusKind, COLS[3]),
    ],
  });
}

function vrow(item, siteShows, docShows, statusLabel, statusKind) {
  return new TableRow({
    cantSplit: true,
    children: [
      cell(item, { width: VCOLS[0], bold: true, size: 18, color: NAVY }),
      cell(siteShows, { width: VCOLS[1], size: 17 }),
      cell(docShows, { width: VCOLS[2], size: 17 }),
      statusCell(statusLabel, statusKind, VCOLS[3]),
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

// ---------- CONTENT: Sections 1-7 (connections, corrected) ----------

const outboundRows = [
  row('Thu 10 Sep', 'WLG → SYD', 'QF162 (Qantas), 6:05am→7:45am, Business – Gary & Karen only (Debbie & Tom join the group in Sydney)', 'Booked', 'ok'),
  row('Thu 10 Sep', 'Sydney connection', 'Arrive T1 7:45am → depart T1 2:45pm (~7 hr layover, same terminal, no hotel/day-room booked)', 'Long layover – confirm plan', 'warn'),
  row('Thu 10 Sep', 'SYD → SIN', 'QF1 (Qantas), 2:45pm→9:15pm, Premium Economy, all 4', 'Booked', 'ok'),
  row('Thu 10 Sep', 'Singapore connection', 'Arrive T1 9:15pm → depart T1 11:20/11:25pm (~2 hr, Qantas → British Airways, both oneworld)', 'Confirm bags check through to FCO', 'warn'),
  row('Thu 10–Fri 11 Sep', 'SIN → LHR', 'BA12 (British Airways), 11:20/11:25pm→6:35am +1, Premium Economy, all 4', 'Booked', 'ok'),
  row('Fri 11 Sep', 'Heathrow connection', 'Arrive T5 6:35am → depart T5 8:00am – ~1 hr 25 min (85 min), same terminal. BA’s minimum connection time at Heathrow T5 is 75 minutes (raised from 60 min in Jan 2024), so this clears the minimum but only by about 10 minutes.', 'TIGHT – meets BA minimum (just)', 'warn'),
  row('Fri 11 Sep', 'LHR → FCO', 'BA548 (British Airways), 8:00am→11:35am, Business (Gary & Karen) / Economy (Debbie & Tom)', 'Booked', 'ok'),
  row('Fri 11 Sep', 'FCO → The Republic Hotel', 'Private minibus, Fiumicino Airport to Via Gaeta 61, Rome (~30–45 min)', 'No confirmation/booking reference on file – confirm with Lynaire', 'warn'),
];

const romeCruiseRows = [
  row('Mon 14 Sep', 'The Republic Hotel → Civitavecchia', 'Private minibus to Queen Victoria cruise terminal – 12pm pickup, evening departure (confirmed via the updated Travel Documents, itinerary note dated 21 Aug 2026)', 'Booked – 12pm pickup confirmed', 'ok'),
  row('Mon 14 Sep', 'Board Queen Victoria', 'Cunard voyage V618D – Deck 8 (Balcony), cabins 8118 (Gary & Karen) and 8112 (Debbie & Tom); booking no. CNZ-83509 – corrected from 4025/4031 (Deck 4) in the previous version of this audit, per the Deck 8 plan confirmed this update', 'Booked', 'ok'),
  row('16–19 Sep', 'Shore excursions', 'Marseille, Villefranche, Genoa, La Spezia (Pisa) – all booked via Cunard Shore Excursions', 'Booked', 'ok'),
];

const carRows = [
  row('Mon 21 Sep', 'Civitavecchia → collect hire car', 'Avis Mercedes Vito (manual transmission), booking ref NZ759149602, at the cruise terminal – vehicle changed from the automatic Ford Kuga SUV in the original 14 Jan quote; confirm whoever drives is comfortable with a manual gearbox', 'Booked – note transmission change', 'warn'),
  row('21–24 Sep', 'Self-drive: Civitavecchia → Talamone → Tuscany → Milan', 'Own hire car for the whole overland leg – no separate transfer booking needed', 'In hand (self-drive)', 'ok'),
  row('Thu 24 Sep', 'Milan → return hire car', 'Return Mercedes Vito at Milan Linate Airport before the flight (4-day hire, Mon 21–Thu 24, confirmed in the 19 Aug Travel Documents – corrected from Wed 23 Sep in the previous version of this audit)', 'Booked', 'ok'),
];

const milanLondonRows = [
  row('Thu 24 Sep', 'LIN → LHR', 'BA575 (British Airways), 3:55pm→4:50pm, Business, all 4 – site corrected from an earlier 2:30pm/2:50pm error (see Section 8)', 'Booked', 'ok'),
  row('Thu 24 Sep', 'Heathrow (T5) → The Level, Meliá White House', 'Site now shows the reconciled version: Luxury Private Vehicle transfer via The Traveling Group / London Travel In (office +44 (0)20 8049 4300, emergency +44 7733 448902), plus booking ref 190826 appended. Re-timed to ~5:15pm pickup given the corrected 4:50pm landing.', 'Booked – reconciled with official document', 'ok'),
  row('Thu 24 Sep', 'Tight evening connection', 'With the corrected flight/transfer timing, hotel arrival is now ~6:00pm, only ~30 min before the 6:30pm Lighterman dinner booking – "Tapas & Gin for Deb" likely won\'t fit', 'Decide: skip pre-dinner drinks or move dinner booking', 'warn'),
];

const londonRows = [
  row('Sun 27 Sep', 'Meliá White House → Heathrow (T5)', 'Leave hotel 7:00pm for 10:00pm BA15 departure – no transfer mode confirmed', 'NOT CONFIRMED – confirm transfer to airport', 'gap'),
];

const returnRows = [
  row('Sun 27–Mon 28 Sep', 'LHR → SIN', 'BA15 (British Airways), 10:00pm→6:40pm +1, Premium Economy, all 4', 'Booked', 'ok'),
  row('Mon 28 Sep', 'Singapore turnaround', 'Arrive T1 6:40pm → depart T1 8:20pm (~1 hr 40 min) – same flight number (BA15) continuing to Sydney', 'Confirm re-boarding process at Changi', 'warn'),
  row('Mon 28–Tue 29 Sep', 'SIN → SYD', 'BA15 (British Airways), 8:20pm→6:05am +1, Premium Economy, all 4', 'Booked', 'ok'),
  row('Tue 29 Sep', 'Sydney – trip ends for Debbie & Tom', 'Arrive T1 6:05am – Sydney is home, no further connection needed', 'N/A', 'ok'),
  row('Tue 29 Sep', 'Sydney connection (Gary & Karen only)', 'Arrive T1 6:05am → depart T1 9:35am (~3 hr 30 min, same terminal)', 'Booked', 'ok'),
  row('Tue 29 Sep', 'SYD → WLG', 'QF161 (Qantas), 9:35am→3:45pm, Economy, Gary & Karen only', 'Booked', 'ok'),
];

const otherRows = [
  row('Ongoing', 'UK Electronic Travel Authorisation', 'Required for all 4 NZ passport holders, £16 each, enforced from 25 Feb 2026', 'Verify all 4 applied/approved via site checklist', 'warn'),
  row('Ongoing', 'Passport validity', 'Needs 6+ months’ validity remaining at end of trip (29 Sep 2026) – valid to at least 29 Mar 2027', 'Verify all 4 checked via site checklist', 'warn'),
  row('Ongoing', 'International Driving Permit (IDP)', 'Whoever drives in Italy needs a valid IDP alongside their licence – Gary\'s is confirmed (IDP196978); Karen, Debbie and Tom not yet ticked', 'Verify remaining 3 via site checklist', 'warn'),
];

// ---------- CONTENT: Section 8 - variations vs official Travel Documents (19 Aug 2026) ----------

const variationRows = [
  vrow(
    'BA575 Milan→London flight time',
    'FIXED: day-24 schedule event, the day-route map note, and the London Things-to-Do note now all say the flight departs 3:55pm, arrives 4:50pm',
    'Official Travel Documents (19 Aug) and the Flight Summary/Connections Audit: BA575 departs 3:55pm, arrives 4:50pm, Business, all 4',
    'Corrected – now matches',
    'ok'
  ),
  vrow(
    'Heathrow → hotel transfer supplier',
    'FIXED: site now shows the Luxury Private Vehicle transfer via The Traveling Group / London Travel In, with booking ref 190826 appended, re-timed to ~5:15pm pickup',
    'Official Travel Documents show a "Luxury Private Vehicle" transfer via The Traveling Group / London Travel In – office +44 (0)20 8049 4300, emergency +44 7733 448902 – no ref number given in the document itself',
    'Reconciled – official supplier + ref kept together',
    'ok'
  ),
  vrow(
    'Hire car return date',
    'Site (and this document, now corrected) show the Avis Mercedes Vito returned Thu 24 Sep at Milan Linate',
    'Official Travel Documents confirm a 4-day hire, Mon 21 – Thu 24 Sep',
    'Matches after correction in this update',
    'ok'
  ),
  vrow(
    'Traveller name – Deb Gyde',
    'FIXED: site now uses "Deb Gyde" consistently everywhere (checklists, flight-summary legend, Emergency Contacts, front-cover credit line)',
    'Official Travel Documents use "Deborah Gyde" (her booking/passport name) – "Deb" is Gary\'s preferred everyday short form',
    'Standardised site-wide – booking name unaffected',
    'ok'
  ),
  vrow(
    'Travel advisor name spelling',
    'FIXED: site\'s Things to Do note now spells the name "Lynaire" (one N)',
    'Official Travel Documents and her email confirm "Lynaire Monnery" (one N), lynaire.monnery@envoyage.co.nz',
    'Corrected – now matches',
    'ok'
  ),
  vrow(
    'Avis Mercedes Vito booking reference',
    'Site shows booking ref NZ759149602',
    'Official Travel Documents confirm the same reference, NZ759149602',
    'Confirmed match',
    'ok'
  ),
  vrow(
    'The Republic Hotel (Rome) details',
    'Address, phone (+39 06 8115 7001) and dates (11–14 Sept) shown in Hotel Directory',
    'Official Travel Documents confirm same address/phone/dates, plus booking refs 5179180 (Gary & Karen) and 5179179 (Debbie & Tom)',
    'FIXED – booking refs 5179180 / 5179179 now shown in Hotel Directory',
    'ok'
  ),
  vrow(
    'Hotel Borgo di Cortefreda Relais details',
    'Address, phone (+39 055 807 3333) and dates (21–23 Sept) shown in Hotel Directory',
    'Official Travel Documents confirm same address/phone/dates, plus booking refs 900422765/900422785 and hotel confirmation numbers 45873846/45873847',
    'FIXED – booking refs 900422765 / 900422785 (confs. 45873846/45873847) now shown in Hotel Directory',
    'ok'
  ),
  vrow(
    'iQ Hotel Milano details',
    'Address, phone (+39 02 8498 0810) and dates (23–24 Sept) shown in Hotel Directory',
    'Official Travel Documents list two different phone numbers internally (+39 02 4550461 in the header block vs 39-02-84980810 in the booking remarks) – site matches the booking-remarks number. Booking refs 9079750869671/9074737872483, confirmations 2385198897/2385198904',
    'FIXED – booking refs 9079750869671 / 9074737872483 (confs. 2385198897/2385198904) now shown in Hotel Directory',
    'ok'
  ),
  vrow(
    'The Level at Meliá White House details',
    'Address, phone (+44 20 7391 3000) and dates (24–27 Sept) shown in Hotel Directory',
    'Official Travel Documents confirm same address/phone/dates, plus booking refs 702Lb92xxk (Gary & Karen) and 702Hpxuze6 (Debbie & Tom)',
    'FIXED – booking refs 702Lb92xxk / 702Hpxuze6 now shown in Hotel Directory',
    'ok'
  ),
  vrow(
    'Traveller list (4 adults)',
    'Site groups Karen & Gary Nicholson, and Deborah Gyde & Thomas Akhurst throughout',
    'Official Travel Documents confirm the same 4 travellers and pairing',
    'Confirmed match',
    'ok'
  ),
  vrow(
    'Fiumicino → Republic Hotel transfer',
    'Site and previous version of this audit both say "arranged in principle, no booking reference on file"',
    'Not in the confirmed 23-page itinerary at all. The original 14 Jan quote did include it (Private Minibus via Destination Italia, indicative cancellation charge $246.14) – see the separate Itinerary Comparison document',
    'Still needs to be booked/confirmed – no change',
    'warn'
  ),
  vrow(
    'Rome hotel → Civitavecchia transfer',
    'FIXED: site now shows a 12pm pickup, status Booked (see Section 2)',
    'Updated Travel Documents (itinerary note dated 21 Aug 2026) confirm "** 12PM pick up **" for the private minibus transfer',
    'Corrected – now matches',
    'ok'
  ),
  vrow(
    'Vatican tour (Sat 12 Sep) & Colosseum tour (Sun 13 Sep)',
    'FIXED: site now shows the Vatican Museums & Sistine Chapel Tour (Towns of Italy, Booking Ref 5CJM745M, 7:45am start) and the Colosseum, Roman Forum & Palatine Hill Tour (Gray Line Rome, Booking ID 202645831, 2:30pm start), each with its own confirmation voucher and QR code on the day card',
    'Individual tour vouchers uploaded separately confirm: Vatican – Towns of Italy, Ref 5CJM745M, 07:45am, meeting point Viale Vaticano; Colosseum – Gray Line Rome, Booking ID 202645831, 2:30pm, meeting point Colle Oppio Park. Previous "Pristine Sistine"/"Arena Floor & VIP Caesar\'s Palace" (Walks of Italy) listings were incorrect and have been replaced',
    'Corrected – real bookings now shown, with voucher QR codes',
    'ok'
  ),
  vrow(
    'Tower of London + Crown Jewels + River Tour combo (Sat 26 Sep)',
    'Trip at a Glance still shows Sat 26 Sep as UNCONFIRMED; Things to Do lists it as "To be confirmed by Jennifer from Headout"',
    'Checked the garrison.co.nz mailbox for a reply from jennifer@inspire.headout.com – no booking confirmation found, only an earlier guidance thread on how to book. Six the Musical (same day, 4:00pm) is booked separately and confirmed – Headout booking #32832547',
    'Still needs to be confirmed – no change',
    'warn'
  ),
  vrow(
    'Travel Documents file',
    'Site\'s Travel Docs button/QR now link to the updated document ("Transfers and Tours Added"), issued 21 Aug 2026 – supersedes the 19 Aug version',
    'Updated Travel Documents (21 Aug 2026) add confirmed transfer times and the Vatican/Colosseum tour details cross-checked above',
    'Replaced – now current',
    'ok'
  ),
  vrow(
    'After-hours Emergency Assist number',
    'Not shown anywhere on the website',
    'Official Travel Documents list an After-hours Emergency Assist line: 0800 232 666 (NZ) / +1 201 746 5104 (overseas)',
    'Missing from site – add to Emergency Contacts',
    'gap'
  ),
];

const gaps = [
  'Meliá White House → Heathrow transfer (Sun 27 Sep): no transfer mode confirmed for the 7:00pm hotel departure.',
  'Fiumicino → Republic Hotel transfer (Fri 11 Sep): arranged in principle but no booking reference is on file, and it doesn\'t appear in the confirmed 23-page itinerary at all – only in the original 14 Jan quote.',
  'Tower of London + Crown Jewels + River Tour combo (Sat 26 Sep): still not confirmed – checked the garrison.co.nz mailbox for a reply from Jennifer at Headout, found only a guidance thread, no booking confirmation.',
  'After-hours Emergency Assist number: 0800 232 666 (NZ) / +1 201 746 5104 (overseas), given in the official Travel Documents but missing from the website – add to Emergency Contacts.',
];

const warnings = [
  'Sydney layover on the way out (Thu 10 Sep, ~7 hrs): RESEARCHED – you can leave the airport. NZ passport holders get a Special Category (subclass 444) visa automatically on arrival, and 7 hrs comfortably clears the ~5 hr minimum needed to get into the city and back (allow ~45 min immigration, ~60 min security).',
  'Singapore connection on the way out (Thu 10 Sep, ~2 hrs): changes airline from Qantas to British Airways – confirm baggage is checked through to Rome.',
  'Heathrow connection on the way out (Fri 11 Sep, ~1 hr 25 min / 85 min): a tight turnaround after a 13+ hour flight. BA’s minimum connection time at T5 is 75 minutes, so this clears it – but only by about 10 minutes, with no margin for a late arrival.',
  'Singapore turnaround on the way home (Mon 28 Sep, ~1 hr 40 min, BA15): RESEARCHED – everyone must deplane at Changi with carry-on items (no staying onboard), and must re-clear security before the Sydney sector (security is at the gate). No passport control needed on a through-checked single ticket. Queues can be long as the whole aircraft transits together.',
  'Thu 24 Sep evening (Milan→London day): with the corrected BA575/transfer timing, hotel arrival is now ~6:00pm – only ~30 min before the 6:30pm Lighterman booking. "Tapas & Gin for Deb" likely won\'t fit; decide whether to skip it or move the dinner booking.',
  'UK ETA, passport validity and IDP: all have checklists on the website, but this document can’t see whether every box is ticked – worth a final look before departure.',
  'Hire car is a manual Mercedes Vito (changed from the automatic Ford Kuga SUV in the original quote) – confirm whoever\'s driving in Italy is comfortable with a manual gearbox.',
];

const children = [];

children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 40 },
  children: [new TextRun({ text: 'FAB4 Does Europe', bold: true, color: NAVY, size: 56, font: 'Prototype' })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 300 },
  children: [new TextRun({ text: 'Audit – Connections, Transfers & Travel Documents – September 2026', bold: true, color: BLUE, size: 28, font: 'Source Sans Pro' })],
}));

children.push(new Paragraph({
  spacing: { after: 240 },
  children: [new TextRun({
    text: 'This document lists every flight, ship, hire-car and transfer connection across the whole trip (10-29 September 2026), in order, with its current booking status (Sections 1-7). Section 8 cross-checks the website against the official Infinity Holidays / Envoyage Travel Documents, most recently updated 21 Aug 2026 with confirmed transfers and tour details added, and lists every variation found. Anywhere a connection or detail needs action is called out clearly - see the summary on the last page.',
    color: INK, size: 19, font: 'Source Sans Pro',
  })],
}));

children.push(sectionHeading('1. Outbound – Wellington to Rome (10–11 Sept)'));
children.push(table(outboundRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('2. Rome to the Cunard cruise (11–14 Sept)'));
children.push(table(romeCruiseRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('3. Cruise, hire car and the overland leg (14–24 Sept)'));
children.push(table(carRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('4. Milan to London (24 Sept)'));
children.push(table(milanLondonRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('5. London departure (27 Sept)'));
children.push(table(londonRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('6. Return – London to Wellington (27–29 Sept)'));
children.push(table(returnRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(sectionHeading('7. Travel documents (ETA, passport, IDP)'));
children.push(table(otherRows, ['Date', 'Connection', 'Details', 'Status'], COLS, COLS_SUM));

children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(sectionHeading('8. Website vs official Travel Documents (updated 21 Aug 2026) – variations found'));
children.push(lede('Cross-checked against "Travel Documents for Nicholson-Gyde and Akhurst" (Infinity Holidays / Envoyage, Booking ID 8381895, issued 19 Aug 2026, updated with transfers and tours added 21 Aug 2026), plus the individual Vatican Museums and Colosseum tour vouchers.'));
children.push(table(variationRows, ['Item', 'Site currently shows', 'Official document shows', 'Status'], VCOLS, VCOLS_SUM));

children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(sectionHeading('Summary: items that still need action'));
children.push(new Paragraph({
  spacing: { after: 140 },
  children: [new TextRun({ text: 'These are flagged in red above – a booking, confirmation or correction is needed:', color: INK, size: 19, font: 'Source Sans Pro' })],
}));
gaps.forEach(g => {
  children.push(new Paragraph({
    spacing: { after: 100 },
    indent: { left: 260 },
    children: [
      new TextRun({ text: '■ ', bold: true, color: RED, size: 19, font: 'Source Sans Pro' }),
      new TextRun({ text: g, color: INK, size: 19, font: 'Source Sans Pro' }),
    ],
  }));
});

children.push(new Paragraph({
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text: 'Worth a closer look (flagged in amber above) – nothing critical, but tight or worth double-checking:', color: INK, size: 19, font: 'Source Sans Pro' })],
}));
warnings.forEach(w => {
  children.push(new Paragraph({
    spacing: { after: 100 },
    indent: { left: 260 },
    children: [
      new TextRun({ text: '■ ', bold: true, color: AMBER, size: 19, font: 'Source Sans Pro' }),
      new TextRun({ text: w, color: INK, size: 19, font: 'Source Sans Pro' }),
    ],
  }));
});

children.push(new Paragraph({
  spacing: { before: 280 },
  children: [new TextRun({
    text: 'Everything else - all flights, the cruise booking, the hire car, the Sydney/Wellington domestic connections, and every hotel\'s address/phone/dates - is booked and confirmed, and matches the official Travel Documents (see Flight Summary, Hotel Directory and Travel Documents on the website for the full reference numbers).',
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
            new TextRun({ text: `   |   Printed: ${dd}/${mm}/${yyyy} (Version 2.3)`, size: 12, color: GREY, font: 'Source Sans Pro' }),
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
  fs.writeFileSync('Fab4_Audit_v2.3.docx', buf);
  console.log('Wrote Fab4_Audit_v2.3.docx', buf.length, 'bytes');
});

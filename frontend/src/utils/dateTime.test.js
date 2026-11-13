import { describe, it } from 'node:test';
import assert from 'node:assert';
import { 
  CLINIC_TIMEZONE,
  CLINIC_TIMEZONE_LABEL,
  format12HourTime, 
  format12HourRange, 
  calculateDurationMinutes, 
  getTimePeriod, 
  groupSlotsByPeriod,
  formatReadableDate,
  formatReadableDateTime,
  extractClinicDate,
  extractClinicTime,
  isPastDate
} from './dateTime.js';

describe('dateTime Utility & Timezone Standardization Tests', () => {
  it('should verify configured clinic timezone constants', () => {
    assert.strictEqual(CLINIC_TIMEZONE, 'Asia/Kolkata');
    assert.strictEqual(CLINIC_TIMEZONE_LABEL, 'IST');
  });

  it('should convert 24-hr times to 12-hr format correctly with optional IST suffix', () => {
    assert.strictEqual(format12HourTime('09:00:00'), '09:00 AM');
    assert.strictEqual(format12HourTime('09:30'), '09:30 AM');
    assert.strictEqual(format12HourTime('12:00:00'), '12:00 PM');
    assert.strictEqual(format12HourTime('16:00:00'), '04:00 PM');
    assert.strictEqual(format12HourTime('16:00:00', true), '04:00 PM IST');
    assert.strictEqual(format12HourTime('17:15:00'), '05:15 PM');
    assert.strictEqual(format12HourTime('00:00:00'), '12:00 AM');
    assert.strictEqual(format12HourTime('23:59:00'), '11:59 PM');
  });

  it('should format 12-hr time range with optional IST suffix', () => {
    assert.strictEqual(
      format12HourRange('09:00:00', '09:30:00'),
      '09:00 AM – 09:30 AM'
    );
    assert.strictEqual(
      format12HourRange('16:00:00', '16:30:00', true),
      '04:00 PM – 04:30 PM IST'
    );
  });

  it('should calculate duration in minutes correctly', () => {
    assert.strictEqual(calculateDurationMinutes('09:00:00', '09:30:00'), 30);
    assert.strictEqual(calculateDurationMinutes('10:00:00', '11:15:00'), 75);
    assert.strictEqual(calculateDurationMinutes('16:00:00', '16:45:00'), 45);
  });

  it('should categorize time into morning, afternoon, and evening', () => {
    assert.strictEqual(getTimePeriod('08:00:00'), 'morning');
    assert.strictEqual(getTimePeriod('11:59:00'), 'morning');
    assert.strictEqual(getTimePeriod('12:00:00'), 'afternoon');
    assert.strictEqual(getTimePeriod('16:00:00'), 'afternoon');
    assert.strictEqual(getTimePeriod('17:00:00'), 'evening');
    assert.strictEqual(getTimePeriod('21:30:00'), 'evening');
  });

  it('should group slots by period and sort chronologically', () => {
    const slots = [
      { id: '1', start_time: '14:00:00' },
      { id: '2', start_time: '09:30:00' },
      { id: '3', start_time: '18:00:00' },
      { id: '4', start_time: '09:00:00' }
    ];

    const grouped = groupSlotsByPeriod(slots);
    assert.strictEqual(grouped.morning.length, 2);
    assert.strictEqual(grouped.morning[0].start_time, '09:00:00');
    assert.strictEqual(grouped.morning[1].start_time, '09:30:00');

    assert.strictEqual(grouped.afternoon.length, 1);
    assert.strictEqual(grouped.afternoon[0].start_time, '14:00:00');

    assert.strictEqual(grouped.evening.length, 1);
    assert.strictEqual(grouped.evening[0].start_time, '18:00:00');
  });

  it('MANDATORY TEST CASE: 11 Nov 2026 10:30 UTC formats to 04:00 PM IST', () => {
    const utcIsoZ = '2026-11-11T10:30:00Z';
    const utcIsoOffset = '2026-11-11T10:30:00+00:00';

    const formattedZ = formatReadableDateTime(utcIsoZ);
    const formattedOffset = formatReadableDateTime(utcIsoOffset);

    assert.strictEqual(formattedZ, 'Wed, Nov 11, 2026 at 04:00 PM IST');
    assert.strictEqual(formattedOffset, 'Wed, Nov 11, 2026 at 04:00 PM IST');

    // Without timezone label
    assert.strictEqual(formatReadableDateTime(utcIsoZ, false), 'Wed, Nov 11, 2026 at 04:00 PM');
  });

  it('EDGE CASE: Midnight boundary across days (20:30 UTC -> 02:00 AM IST next day)', () => {
    const utcInstant = '2026-11-11T20:30:00Z';
    const formatted = formatReadableDateTime(utcInstant);
    assert.strictEqual(formatted, 'Thu, Nov 12, 2026 at 02:00 AM IST');

    assert.strictEqual(extractClinicDate(utcInstant), '2026-11-12');
    assert.strictEqual(extractClinicTime(utcInstant), '02:00:00');
  });

  it('EDGE CASE: Month boundary (30 Nov 2026 20:30 UTC -> 01 Dec 2026 02:00 AM IST)', () => {
    const utcInstant = '2026-11-30T20:30:00Z';
    const formatted = formatReadableDateTime(utcInstant);
    assert.strictEqual(formatted, 'Tue, Dec 1, 2026 at 02:00 AM IST');

    assert.strictEqual(extractClinicDate(utcInstant), '2026-12-01');
    assert.strictEqual(extractClinicTime(utcInstant), '02:00:00');
  });

  it('should extract clinic date and time accurately from UTC ISO string', () => {
    const utcInstant = '2026-11-11T10:30:00Z';
    assert.strictEqual(extractClinicDate(utcInstant), '2026-11-11');
    assert.strictEqual(extractClinicTime(utcInstant), '16:00:00');
  });

  it('should format readable calendar dates without timezone shift', () => {
    const formatted = formatReadableDate('2026-11-11');
    assert.strictEqual(formatted, 'Wed, Nov 11, 2026');
  });

  it('should detect past dates correctly', () => {
    assert.strictEqual(isPastDate('2020-01-01'), true);
    assert.strictEqual(isPastDate('2099-12-31'), false);
  });
});

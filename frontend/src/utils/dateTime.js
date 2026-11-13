/**
 * Medicall Date & Time Utility Functions
 * Establishes strict timezone standardization:
 * - Patient-Facing / Clinic Timezone: Asia/Kolkata (IST, UTC+05:30)
 * - Strict 12-hour AM/PM formatting with optional 'IST' timezone label
 * - ISO UTC parsing into Asia/Kolkata regardless of user browser timezone
 */

export const CLINIC_TIMEZONE = 'Asia/Kolkata';
export const CLINIC_TIMEZONE_LABEL = 'IST';

/**
 * Converts a 24-hour time string ("HH:MM" or "HH:MM:SS") into a 12-hour AM/PM string ("hh:mm AM/PM").
 * Examples: "09:00:00" -> "09:00 AM", "16:00:00" -> "04:00 PM", "16:00:00" (with includeTz=true) -> "04:00 PM IST"
 */
export const format12HourTime = (timeStr, includeTz = false) => {
  if (!timeStr) return '';
  const parts = String(timeStr).split(':');
  if (parts.length < 2) return timeStr;

  let hour = parseInt(parts[0], 10);
  const minute = parts[1].padStart(2, '0');
  if (isNaN(hour)) return timeStr;

  const period = hour >= 12 ? 'PM' : 'AM';
  hour = hour % 12;
  if (hour === 0) hour = 12;
  const hourStr = String(hour).padStart(2, '0');

  const tzSuffix = includeTz ? ` ${CLINIC_TIMEZONE_LABEL}` : '';
  return `${hourStr}:${minute} ${period}${tzSuffix}`;
};

/**
 * Formats a start and end time string into a 12-hour range.
 * Example: ("16:00:00", "16:30:00") -> "04:00 PM – 04:30 PM"
 */
export const format12HourRange = (startTime, endTime, includeTz = false) => {
  if (!startTime) return '';
  const start = format12HourTime(startTime, false);
  if (!endTime) return includeTz ? `${start} ${CLINIC_TIMEZONE_LABEL}` : start;
  const end = format12HourTime(endTime, includeTz);
  return `${start} – ${end}`;
};

/**
 * Calculates duration in minutes between two 24-hr time strings.
 * Example: ("09:00", "09:30") -> 30
 */
export const calculateDurationMinutes = (startTime, endTime) => {
  if (!startTime || !endTime) return 30;
  const [h1, m1] = startTime.split(':').map(Number);
  const [h2, m2] = endTime.split(':').map(Number);
  if (isNaN(h1) || isNaN(m1) || isNaN(h2) || isNaN(m2)) return 30;
  return (h2 * 60 + m2) - (h1 * 60 + m1);
};

/**
 * Categorizes a time string into Morning, Afternoon, or Evening.
 * Morning:   06:00 AM – 11:59 AM (hour 6 to 11)
 * Afternoon: 12:00 PM – 04:59 PM (hour 12 to 16)
 * Evening:   05:00 PM – 11:59 PM (hour 17 to 23, or 0 to 5)
 */
export const getTimePeriod = (timeStr) => {
  if (!timeStr) return 'morning';
  const hour = parseInt(String(timeStr).split(':')[0], 10);
  if (isNaN(hour)) return 'morning';

  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  return 'evening';
};

/**
 * Groups an array of slot objects into morning, afternoon, and evening buckets.
 * Expected slot object format: { start_time: "09:00:00", ... }
 */
export const groupSlotsByPeriod = (slots = []) => {
  const groups = {
    morning: [],
    afternoon: [],
    evening: [],
  };

  slots.forEach((slot) => {
    const period = getTimePeriod(slot.start_time);
    if (groups[period]) {
      groups[period].push(slot);
    } else {
      groups.morning.push(slot);
    }
  });

  // Sort slots inside each period chronologically
  const sortByStart = (a, b) => (a.start_time > b.start_time ? 1 : -1);
  groups.morning.sort(sortByStart);
  groups.afternoon.sort(sortByStart);
  groups.evening.sort(sortByStart);

  return groups;
};

/**
 * Formats a Date, "YYYY-MM-DD" string, or ISO timestamp into readable format:
 * "Wed, Nov 11, 2026"
 * Pure calendar dates ("YYYY-MM-DD") are preserved without timezone shift.
 * ISO timestamps are explicitly evaluated in Asia/Kolkata timezone.
 */
export const formatReadableDate = (dateInput) => {
  if (!dateInput) return '';
  if (typeof dateInput === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateInput)) {
    const [year, month, day] = dateInput.split('-').map(Number);
    const dateObj = new Date(Date.UTC(year, month - 1, day, 12, 0, 0));
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC'
    }).format(dateObj);
  }

  const dateObj = new Date(dateInput);
  if (isNaN(dateObj.getTime())) return String(dateInput);

  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: CLINIC_TIMEZONE
  }).format(dateObj);
};

/**
 * Formats a datetime ISO string (e.g. "2026-11-11T10:30:00Z" or "2026-11-11T10:30:00+00:00")
 * into Asia/Kolkata local appointment display:
 * "Wed, Nov 11, 2026 at 04:00 PM IST"
 */
export const formatReadableDateTime = (isoString, includeTz = true) => {
  if (!isoString) return '';
  const dateObj = new Date(isoString);
  if (isNaN(dateObj.getTime())) return String(isoString);

  const datePart = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: CLINIC_TIMEZONE,
  }).format(dateObj);

  const timePart = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZone: CLINIC_TIMEZONE,
  }).format(dateObj);

  const tzSuffix = includeTz ? ` ${CLINIC_TIMEZONE_LABEL}` : '';
  return `${datePart} at ${timePart}${tzSuffix}`;
};

/**
 * Extracts "YYYY-MM-DD" calendar date in Asia/Kolkata timezone from an ISO string.
 * Example: "2026-11-11T20:30:00Z" -> "2026-11-12" (since 20:30 UTC = 02:00 IST next day)
 */
export const extractClinicDate = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return '';
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: CLINIC_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(d);
};

/**
 * Extracts 24-hr "HH:MM:SS" time in Asia/Kolkata timezone from an ISO string.
 * Example: "2026-11-11T10:30:00Z" -> "16:00:00" (04:00 PM IST)
 */
export const extractClinicTime = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return '';
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: CLINIC_TIMEZONE,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(d);
};

/**
 * Converts a Date object to "YYYY-MM-DD" local date string
 */
export const toLocalDateString = (dateObj) => {
  if (!dateObj || isNaN(dateObj.getTime())) return '';
  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, '0');
  const day = String(dateObj.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Checks if two date inputs represent the same calendar day.
 */
export const isSameDay = (date1, date2) => {
  if (!date1 || !date2) return false;
  const d1Str = typeof date1 === 'string' ? date1.split('T')[0] : toLocalDateString(date1);
  const d2Str = typeof date2 === 'string' ? date2.split('T')[0] : toLocalDateString(date2);
  return d1Str === d2Str;
};

/**
 * Checks if a date string is in the past (before today's local date).
 */
export const isPastDate = (dateStr) => {
  if (!dateStr) return false;
  const todayStr = toLocalDateString(new Date());
  return dateStr < todayStr;
};

import axios from 'axios';

// In production (Vercel), set REACT_APP_API_URL to your Railway backend URL
// e.g. https://your-app.up.railway.app
// Locally, falls back to http://localhost:8000
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const API = axios.create({ baseURL: BASE_URL });

API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

/**
 * Normalize any axios / FastAPI error into a plain displayable string.
 * FastAPI 422 validation errors return:
 *   { detail: [ { type, loc, msg, input, ctx }, ... ] }
 * which cannot be rendered directly as a React child (causes
 * "Objects are not valid as a React child").
 */
export function getApiError(e, fallback = 'Something went wrong') {
  const detail = e?.response?.data?.detail;

  // FastAPI string detail, e.g. { detail: "Incorrect credentials" }
  if (typeof detail === 'string') return detail;

  // FastAPI Pydantic v2 validation errors: array of { type, loc, msg, ... }
  if (Array.isArray(detail) && detail.length > 0) {
    const parts = detail.map(d => {
      const loc = Array.isArray(d?.loc) ? d.loc.join('.') : '';
      return (loc ? `${loc}: ` : '') + (d?.msg || 'Invalid value');
    });
    return parts.join('; ');
  }

  // Some backends embed the message in an object/array under detail.msg
  if (typeof detail?.msg === 'string') return detail.msg;

  // Network / server errors with no structured body
  if (!e?.response) {
    return e?.message || fallback;
  }

  return fallback;
}

export default API;
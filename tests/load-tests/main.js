import { thresholds } from './config/thresholds.js';
import { runDocumentQuery } from './scenarios/document-query.js';
import { runDocumentUpload } from './scenarios/document-upload.js';

export const options = {
    scenarios: {
        // Stage 1: Clean Baseline (Only Q&A queries)
        baseline_query: {
            executor: 'constant-vus',
            exec: 'documentQueryScenario',
            vus: 5,
            duration: '2m',
            startTime: '0s',
        },
        // Stage 2: Separate File Upload Test
        document_upload: {
            executor: 'constant-vus',
            exec: 'documentUploadScenario',
            vus: 5,
            duration: '2m',
            startTime: '2m15s',          // Starts AFTER baseline finishes
        },
        // Stage 3: Peak Load Capacity Test
        peak_query: {
            executor: 'ramping-vus',
            exec: 'documentQueryScenario',
            startVUs: 0,
            stages: [
                { duration: '2m', target: 5 },
                { duration: '3m', target: 5 },
                { duration: '1m', target: 5 },
            ],
            startTime: '4m30s',          // Starts AFTER upload scenario completes
        }
    },
    thresholds: thresholds,
};

// const BASE_URL = "https://ttt-rc5.talkingdb.io";
const BASE_URL = "http://localhost:8090";
const API_KEY = __ENV.API_KEY;
const GRAPH_ID = __ENV.GRAPH_ID;

if (!API_KEY) {
    throw new Error('API_KEY is required');
}

if (!GRAPH_ID) {
    throw new Error('GRAPH_ID is required');
}

export function documentUploadScenario() {
    runDocumentUpload(BASE_URL, API_KEY);
}

export function documentQueryScenario() {
    runDocumentQuery(BASE_URL, API_KEY, GRAPH_ID);
}
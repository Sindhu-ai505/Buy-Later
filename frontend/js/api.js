/**
 * BuyLater Frontend API Client
 * Connects vanilla JS pages with the FastAPI backend.
 */

// Dynamically determine API base URL (works whether opened on port 8000 or file/live-server)
const API_BASE = window.location.port === "8000" 
  ? window.location.origin 
  : "http://127.0.0.1:8000";

// Default active user ID (Demo user seeded on startup: 1)
const CURRENT_USER_ID = 1;

/** Generic fetch helper with JSON error handling */
async function apiRequest(endpoint, options = {}) {
  try {
    const url = `${API_BASE}${endpoint}`;
    // Attach bypass header for tunnel environments
    const headers = {
      ...(options.headers || {}),
      "Bypass-Tunnel-Reminder": "true",
    };
    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      let errDetail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errDetail = errorData.detail || errDetail;
      } catch (e) {
        errDetail = await response.text();
      }
      throw new Error(errDetail);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    showToast(error.message, true);
    throw error;
  }
}

/** Show temporary toast message */
function showToast(message, isError = false) {
  let toast = document.getElementById("app-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "app-toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.background = isError ? "#e11d48" : "#1e1b4b";
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 4000);
}

// User API
async function getUser(userId = CURRENT_USER_ID) {
  return await apiRequest(`/users/${userId}`);
}

async function getUserPersonality(userId = CURRENT_USER_ID) {
  return await apiRequest(`/users/${userId}/personality`);
}

async function updateUserPersonality(personality, userId = CURRENT_USER_ID) {
  return await apiRequest(`/users/${userId}/personality`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ personality }),
  });
}

// Product Analysis API
async function analyzeProductUrl(url) {
  return await apiRequest("/products/analyze-url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

async function analyzeProductImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return await apiRequest("/products/analyze-image", {
    method: "POST",
    body: formData,
  });
}

async function createProductManual(productData) {
  return await apiRequest("/products/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(productData),
  });
}

// Analysis & Adaptive Questions API
async function startAnalysis(productId, userId = CURRENT_USER_ID) {
  return await apiRequest("/analysis/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, product_id: productId }),
  });
}

async function submitAnswer(analysisId, questionKey, question, answer) {
  return await apiRequest(`/analysis/${analysisId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question_key: questionKey,
      question: question,
      answer: answer,
    }),
  });
}

async function getAnalysisResult(analysisId) {
  return await apiRequest(`/analysis/${analysisId}/result`);
}

async function challengeDecision(analysisId) {
  return await apiRequest(`/analysis/${analysisId}/challenge`, {
    method: "POST",
  });
}

async function initiateWaitRecord(analysisId, waitDays = 7) {
  return await apiRequest(`/analysis/${analysisId}/wait`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wait_days: waitDays }),
  });
}

async function getWaitStatus(analysisId) {
  return await apiRequest(`/analysis/${analysisId}/wait`);
}

async function submitWaitDecision(analysisId, finalDecision) {
  return await apiRequest(`/analysis/${analysisId}/wait/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ final_decision: finalDecision }),
  });
}

// My Stuff Inventory API
async function getMyStuff(userId = CURRENT_USER_ID) {
  return await apiRequest(`/my-stuff/${userId}`);
}

async function addMyStuff(itemData, userId = CURRENT_USER_ID) {
  return await apiRequest("/my-stuff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...itemData, user_id: userId }),
  });
}

async function deleteMyStuff(itemId) {
  return await apiRequest(`/my-stuff/${itemId}`, {
    method: "DELETE",
  });
}

// Purchase History & Feedback API
async function getPurchases(userId = CURRENT_USER_ID) {
  return await apiRequest(`/purchases/${userId}`);
}

async function submitFeedback(analysisId, purchased, satisfaction = null, regret = false) {
  return await apiRequest("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      analysis_id: analysisId,
      purchased: purchased,
      satisfaction: satisfaction,
      regret: regret,
    }),
  });
}

// Dashboard API
async function getDashboard(userId = CURRENT_USER_ID) {
  return await apiRequest(`/dashboard/${userId}`);
}

// Load active user personality into header badge if element exists
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const chip = document.getElementById("nav-personality-badge");
    if (chip) {
      const data = await getUserPersonality();
      chip.textContent = `Persona: ${data.personality}`;
    }
  } catch (e) {
    // Graceful fallback
  }
});

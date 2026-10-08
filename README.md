# BuyLater — "Do I Actually Need This?"
### College Deep Learning Project | Personal Spending-Behavior & Impulse Assessment Assistant

---

## 1. Project Overview & Problem Statement
Online shopping platforms and algorithmic digital marketing are engineered to maximize instant conversions and impulsive purchases. Consumers frequently experience "buyer's remorse," buying duplicate items, stretching discretionary budgets, and acquiring products influenced by artificial discount scarcity.

**BuyLater** is a personal spending-behavior assistant designed to intercept impulse decisions before checkout. By analyzing candidate products (via URL, OCR screenshot, or manual entry), reviewing user inventory ("My Stuff"), auditing past transaction regret, and applying a trained Deep Learning Neural Network, BuyLater produces an explainable **Purchase Score (0–100)**, an **Impulse Risk Probability**, an actionable recommendation (**BUY NOW**, **CONSIDER**, **WAIT 7 DAYS**, or **DON'T BUY**), and offers a 7-day cooling-off period.

---

## 2. Objectives
- **Predict Impulse Probability**: Train and deploy a feed-forward deep neural network (Keras/TensorFlow) that predicts impulse buying risk from behavioral, financial, and context features.
- **Explainable Purchase Scoring**: Combine functional need, expected usage, budget fit, existing inventory overlap, and impulse risk into a transparent score (0–100).
- **Prevent Redundant Buying**: Use explainable keyword & category similarity (no opaque embeddings) to warn users when they already own an adequate substitute.
- **Support Cooling-Off Protocols**: Implement a 7-day wait timer and Devil's Advocate decision challenge to overcome emotional urgency.
- **Custom Persona Tones**: Provide 6 distinct communication styles (Best Friend, Spouse, Parent, Child, Sibling, Professional Advisor) that alter phrasing without skewing mathematical decisions.

---

## 3. Tech Stack
- **Frontend**: HTML5, CSS3 (Modern Responsive Design System), Vanilla JavaScript (Fetch API)
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Database**: SQLite + SQLAlchemy ORM
- **Deep Learning**: TensorFlow 2.15+ / Keras 3 (Sequential Dense Architecture)
- **Data & ML**: Scikit-learn, Pandas, NumPy, joblib
- **OCR Engine**: EasyOCR (+ Pillow)
- **Metadata Extraction**: Requests + BeautifulSoup4
- **Security**: Direct `bcrypt` password hashing (no banking/card credentials stored)
- **Testing**: Pytest + FastAPI TestClient

---

## 4. Architecture & Pipeline
```
[User Input: URL / Screenshot / Manual]
                    │
                    ▼
           Product Extraction (EasyOCR / BeautifulSoup)
                    │
                    ▼
          Review & Confirmation (analyze.html)
                    │
                    ▼
      Adaptive Questions Engine (decision tree, 1 at a time)
                    │
                    ▼
   Feature Engineering (17 behavioral, financial, inventory metrics)
                    │
                    ▼
   Deep Learning Model (Dense(64) -> Dropout -> Dense(32) -> Dense(16) -> Dense(1, Sigmoid))
                    │
                    ▼
        Impulse Probability (0.0 to 1.0)
                    │
                    ▼
  Explainable Scoring Engine (Need 25%, Usage 15%, Budget 20%, Existing 15%, Intent 15%, Behavior 10%)
                    │
                    ▼
   Recommendation & Exceptions (BUY NOW / CONSIDER / WAIT 7 DAYS / DON'T BUY)
                    │
                    ▼
      Personality Layer (Wording & emotional tone only)
                    │
                    ▼
   Decision Actions (Challenge / 7-Day Wait Record / Feedback Logging)
```

---

## 5. Project Structure
```
BuyLater/
├── backend/
│   ├── ai/
│   │   └── impulse_model.py          # Keras model loading & inference
│   ├── routers/
│   │   ├── users.py                  # User profiles & personality
│   │   ├── products.py               # Manual, URL & OCR screenshot entry
│   │   ├── my_stuff.py               # Owned inventory management
│   │   ├── purchases.py              # Purchase transaction history
│   │   ├── analysis.py               # Question flow, DL inference, scoring
│   │   ├── feedback.py               # Post-decision satisfaction & savings
│   │   └── dashboard.py              # Metrics & aggregate AI insights
│   ├── services/
│   │   ├── product_service.py        # EasyOCR & metadata parsing
│   │   ├── my_stuff_service.py       # Explainable inventory similarity
│   │   ├── history_service.py        # Spending and regret statistics
│   │   ├── question_service.py       # Adaptive decision-tree questions
│   │   ├── behavior_service.py       # 17-feature extraction pipeline
│   │   ├── scoring_service.py        # Weighted scoring & recommendations
│   │   ├── challenge_service.py      # Devil's Advocate case for buying
│   │   ├── wait_service.py           # 7-day cooling-off tracking
│   │   └── dashboard_service.py      # Real-data behavior analytics
│   ├── utils/
│   │   ├── personality.py            # 6 persona tone dictionary templates
│   │   └── security.py               # Bcrypt password hashing
│   ├── crud.py                       # SQLAlchemy database operations
│   ├── database.py                   # SQLite engine & session setup
│   ├── models.py                     # SQLAlchemy database models
│   ├── schemas.py                    # Pydantic validation schemas
│   └── main.py                       # FastAPI entrypoint, CORS, static mounts
├── frontend/
│   ├── css/
│   │   └── style.css                 # Clean modern responsive stylesheet
│   ├── js/
│   │   └── api.js                    # Fetch client & state management
│   ├── index.html                    # Landing page with URL, OCR & manual entry
│   ├── analyze.html                  # Review extracted fields before analysis
│   ├── conversation.html             # Chat-style adaptive question interface
│   ├── result.html                   # Score gauge, impulse %, challenge, feedback
│   ├── dashboard.html                # Savings, spending stats & AI insights
│   ├── my-stuff.html                 # Owned inventory tracker
│   ├── history.html                  # Past analyses & cooling-off recheck logs
│   └── settings.html                 # Personality & monthly budget preferences
├── ml/
│   ├── data/
│   │   ├── generate_dataset.py       # Synthetic dataset generation with noise
│   │   └── export_feedback_dataset.py# SQLite feedback exporter for future retraining
│   ├── preprocessing/
│   │   └── preprocess.py             # StandardScaler & OneHotEncoder pipeline
│   ├── training/
│   │   └── train_model.py            # Keras training with EarlyStopping
│   ├── evaluation/
│   │   └── evaluate_model.py         # Accuracy, precision, recall, F1, ROC-AUC
│   └── models/                       # Saved .keras model, scaler & encoders
├── tests/
│   ├── test_basic.py                 # Unit tests (models, OCR, scoring, persona)
│   └── test_end_to_end.py            # Full workflow integration test
├── uploads/                          # Temporary screenshot uploads
├── requirements.txt                  # Python dependencies
├── pytest.ini                        # Pytest configuration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
└── README.md                         # Project documentation & viva guide
```

---

## 6. Installation & Step-by-Step Execution

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Generate Synthetic Dataset
```bash
python ml/data/generate_dataset.py
```
*Creates 3,200 prototype spending records with realistic noise.*

### Step 3: Train the Deep Learning Model
```bash
python ml/training/train_model.py
```
*Trains Keras neural network with early stopping and saves artifacts into `ml/models/`.*

### Step 4: Evaluate the Model
```bash
python ml/evaluation/evaluate_model.py
```
*Outputs Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix.*

### Step 5: Run Pytest Test Suite
```bash
python -m pytest -v
```
*Executes all 8 unit and end-to-end integration tests.*

### Step 6: Start FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend Web App: [http://127.0.0.1:8000/app/index.html](http://127.0.0.1:8000/app/index.html)

---

## 7. Model Evaluation Metrics
Evaluated on 640 unseen stratified test samples:
- **Accuracy**: 85.47%
- **Precision**: 85.24%
- **Recall**: 88.44%
- **F1 Score**: 0.8681
- **ROC-AUC**: 0.9384

The model avoids trivially perfect scores (~100%) due to realistic behavioral noise, reflecting genuine human spending variance.

---

## 8. College Viva & Faculty Q&A Guide

### Q1: Why use Deep Learning instead of basic rule checks?
**Answer**: While scoring rules evaluate explicit linear constraints (e.g. price vs budget), consumer spending behavior exhibits non-linear interactions (e.g., promotional discounts + browsing + high past regret + high recent frequency compounding together). The neural network learns these multi-dimensional interaction surfaces and outputs an objective impulse probability without hardcoded heuristics.

### Q2: What is the Model Architecture and why?
**Answer**: A Feed-Forward Deep Neural Network (MLP) built in Keras:
- **Input Layer**: 23 normalized input units (16 scaled numeric features + 7 one-hot encoded purchase reasons).
- **Dense Layer 1 (64 neurons, ReLU)**: Captures non-linear combinations of financial and behavioral inputs.
- **Dropout (25%)**: Prevents co-adaptation of neurons and reduces overfitting on synthetic patterns.
- **Dense Layer 2 (32 neurons, ReLU)**: Compresses representations into high-level behavioral abstractions.
- **Dense Layer 3 (16 neurons, ReLU)**: Refines decision boundaries.
- **Output Layer (1 neuron, Sigmoid)**: Squashes output between 0.0 and 1.0, representing the calibrated probability of impulse purchase.

### Q3: Why ReLU and Sigmoid activations?
**Answer**:
- **ReLU (Rectified Linear Unit)**: Solves the vanishing gradient problem, computes quickly ($\max(0, x)$), and enables the hidden layers to learn complex non-linear feature combinations.
- **Sigmoid**: Standard activation for binary classification outputs; maps any real-valued number into a smooth probability interval $[0, 1]$.

### Q4: Why Binary Cross-Entropy Loss?
**Answer**: It measures the divergence between actual labels $y \in \{0, 1\}$ and predicted probabilities $\hat{y} \in [0, 1]$:
$$\mathcal{L} = -\frac{1}{N}\sum_{i=1}^N \left[ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) \right]$$
Penalizing confident incorrect predictions heavily, driving optimal probability calibration.

### Q5: How is the final Purchase Score calculated?
**Answer**:
Computed from explainable factors with centralized weights:
- **Need (25%)**: Urgency, problem solved, broken item vs novelty.
- **Usage (15%)**: Anticipated daily/weekly/monthly frequency.
- **Budget (20%)**: Price-to-budget ratio and subjective financial headroom.
- **Existing Product (15%)**: Penalizes redundant working duplicates.
- **Purchase Intent (15%)**: Planning status, damped by Deep Learning impulse probability:
  $$\text{Intent}_{\text{damped}} = \text{Intent}_{\text{base}} \times (1.0 - 0.5 \times P_{\text{impulse}})$$
- **Behavior Discipline (10%)**: Historical regret rate and recent spending velocity, damped by $P_{\text{impulse}}$.

Total Score ranges from 0 to 100.
- **75–100**: BUY NOW
- **50–74**: CONSIDER
- **25–49**: WAIT 7 DAYS
- **0–24**: DON'T BUY
*(Exception: If an essential owned item is broken and the new purchase is a direct functional replacement, the system upgrades recommendation to avoid leaving the user without essentials).*

### Q6: How does OCR work in this project?
**Answer**:
EasyOCR uses a PyTorch deep learning pipeline consisting of:
1. **CRAFT (Character Region Awareness for Text Detection)**: Localizes text boxes in the screenshot.
2. **ResNet + BiLSTM + CTC (Connectionist Temporal Classification)**: Recognizes text strings inside bounding boxes.
Regular expressions then extract currency patterns, discount percentages, and product titles.

### Q7: How does "My Stuff" prevent duplicate purchases?
**Answer**:
Uses explainable, deterministic similarity:
1. Cleans and tokenizes names (stopwords removed).
2. Category match (0.50 score).
3. Keyword Jaccard token overlap (0.50 score).
If similarity exceeds threshold, it alerts the user and adapts question flow (e.g. asking if their current item is broken or working).

### Q8: Does the Personality System alter the Deep Learning prediction?
**Answer**:
**Strictly NO.** The personality layer (`backend/utils/personality.py`) modifies only phrasing, tone, and metaphors. The underlying model weights, probabilities, feature values, and recommendations remain 100% deterministic and unaffected by tone.

### Q9: Why is synthetic data used and what are its limitations?
**Answer**:
Discretionary personal impulse purchases lack open-source labeled consumer behavioral datasets with private budget ratios and inventory context. We generated synthetic prototype data to demonstrate the end-to-end Deep Learning pipeline. It does not represent psychological diagnosis; the feedback loop (`ml/data/export_feedback_dataset.py`) enables future retraining on real user feedback.

---

## 9. Limitations & Future Scope
- **Current Limitations**: Synthetic training baseline; OCR requires clear text contrast; URL scraper relies on OpenGraph and standard meta tags.
- **Future Scope**: Direct integration with UPI/bank statement SMS parsing, barcode scanning via mobile camera, Chrome extension popup on checkout pages, and continuous online retraining with user feedback.

# Analytics & Adaptive Content Architecture

## Overview

This document describes the analytics-driven visualization and adaptive content generation system added to Learnzo.

## 1. Engagement Analytics

### Backend Service (`app/services/engagement_service.py`)

**Architecture**: Clean service layer with no hardcoded thresholds. Scores normalized to 0-100%.

**Components**:
- **Session Duration Score**: Normalized by expected duration (15 minutes baseline)
- **Interaction Frequency Score**: Sessions per week (3/week baseline)
- **Completion Score**: Percentage of sessions with positive feedback
- **Feedback Quality Score**: Weighted average of reward scores (-1 to 1) and engagement ratings (1-5)

**Overall Score**: Weighted average (25% each component)

**API Endpoints** (`app/api/analytics.py`):
- `GET /analytics/engagement/me` - Current student's engagement
- `GET /analytics/engagement/{learner_id}` - Specific learner (teacher/parent)
- `GET /analytics/engagement/aggregate` - All students distribution (teacher)

### Frontend Visualization

**Components** (`frontend/src/components/EngagementChart.tsx`):
- `EngagementChart` - Pie chart for distribution (high/medium/low)
- `EngagementBreakdownChart` - Pie chart for score components

**Integration**:
- Student Dashboard: Shows individual engagement breakdown
- Teacher Dashboard: Shows aggregate distribution across all students

## 2. Content Ranking & Adaptive Generation

### Backend Service (`app/services/content_ranking_service.py`)

**Ranking Algorithm**:
1. **Base Scores**: From VARK assessment (normalized to 0-100)
2. **Disability Adjustments**: Boost preferred styles, penalize disabled modalities
3. **Engagement Adjustments**: Adjust based on historical feedback (positive rewards boost, negative penalize)

**Returns**: Ranked list of (mode, score, reason) tuples

### Content API Extension (`app/api/content.py`)

**New Response Format**:
```json
{
  "session_id": "...",
  "topic": "...",
  "recommended_mode": {
    "mode": "visual",
    "score": 85.5,
    "reason": "Based on VARK assessment (V dominant)"
  },
  "mode_ranking": [
    {"mode": "visual", "score": 85.5, "reason": "..."},
    {"mode": "auditory", "score": 72.0, "reason": "..."},
    ...
  ],
  "content_by_mode": {
    "visual": {...},
    "auditory": {...},
    "reading": {...},
    "kinesthetic": {...}
  }
}
```

**Key Features**:
- Generates content in all 4 VARK modes for every topic
- Ranks modes based on learner profile + engagement
- Returns recommended mode with explanation
- Allows exploration of all modes

## 3. Frontend Content Presentation

### Learning Page (`frontend/src/pages/Learning.tsx`)

**Features**:
- Search bar for topics
- **Recommended Mode Banner**: Clearly highlights top-ranked mode
- **Mode Tabs**: Clickable tabs for all 4 modes (Visual, Auditory, Reading/Writing, Kinesthetic)
- **Content Panels**: Dynamic rendering based on mode:
  - Visual: Images grid
  - Auditory: Text with audio note
  - Reading: Structured text with source
  - Kinesthetic: Activity list
- **Ranking Info**: Shows all modes with scores and reasons

**UI Principles**:
- Child-friendly: Large buttons, clear labels, icons
- Accessibility: High contrast, simple language
- Exploration: Learners can switch modes freely

## 4. Data Flow

```
User searches topic
  ↓
Backend: rank_learning_modes()
  ↓
  - Fetch VARK scores
  - Apply disability constraints
  - Adjust by engagement history
  ↓
Backend: Generate content for all 4 modes
  ↓
Frontend: Display recommended + tabs for all modes
  ↓
User explores different modes
```

## 5. Scoring Decisions

### Engagement Score Weights
- Duration: 25% (measures time investment)
- Frequency: 25% (measures consistency)
- Completion: 25% (measures task completion)
- Feedback: 25% (measures quality/engagement)

### Content Ranking Weights
- VARK base: 60% (initial assessment)
- Disability adjustments: 20% (constraints)
- Engagement adjustments: 20% (learned preferences)

### Thresholds
- High engagement: ≥70%
- Medium engagement: 40-69%
- Low engagement: <40%

## 6. Future Enhancements

- Real-time engagement updates
- A/B testing for content effectiveness
- Machine learning model for mode prediction
- Parent dashboard with individual child engagement

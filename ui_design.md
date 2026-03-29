# UI Design Specifications

## Color Palette

| Color Name      | Hex       | Usage                           |
|-----------------|-----------|---------------------------------|
| Trust Blue      | `#2563eb` | Primary buttons, links          |
| Engagement Blue | `#3b82f6` | Hover states, secondary actions |
| Growth Green    | `#10b981` | Success, resolved status        |
| Caution Orange  | `#f59e0b` | Warning, pending status         |
| Alert Red       | `#ef4444` | Error, escalated status         |
| Slate Gray      | `#64748b` | Secondary text                  |
| Light Gray      | `#f1f5f9` | Backgrounds                     |
| White           | `#ffffff` | Cards, inputs                   |

## Icons (Heroicons Outline)
- **Navigation:** HomeIcon, UserIcon, CogIcon
- **Actions:** PlusIcon, PencilIcon, TrashIcon, MapPinIcon
- **Status:** ClockIcon (pending), CheckCircleIcon (resolved), ExclamationTriangleIcon (escalated)
- **Communication:** BellIcon, ChatBubbleIcon

## Page Layouts

### 1. Login Page
```
+------------------------------------------+
|              [Logo]                       |
|              Sign In                      |
|          +--------------------+          |
|          | Email              |          |
|          +--------------------+          |
|          +--------------------+          |
|          | Password           |          |
|          +--------------------+          |
|          [        Sign In     ]          |
|          Don't have account? Register    |
+------------------------------------------+
```

### 2. User Dashboard
```
+------------------------------------------+
| [Logo] Complaints    [Bell] [User Avatar]|
+------------------------------------------+
|  My Complaints        [+ New Complaint]  |
+------------------------------------------+
| +----------------+  +----------------+   |
| | #CMP-001       |  | #CMP-002       |   |
| | Garbage Dump   |  | Road Damage    |   |
| | [Pending]      |  | [Resolved]     |   |
| | 2 days ago     |  | 5 days ago     |   |
| +----------------+  +----------------+   |
+------------------------------------------+
```

### 3. Complaint Form (with Map)
```
+------------------------------------------+
|         Report a New Issue               |
+------------------------------------------+
| Title: [____________________________]    |
| Category: [Dropdown v]                   |
| Description:                             |
| +------------------------------------+   |
| |                                    |   |
| | (textarea)                         |   |
| +------------------------------------+   |
| Location: [Click on map to select]       |
| +------------------------------------+   |
| |        [Leaflet Map]               |   |
| |              * (selected pin)      |   |
| +------------------------------------+   |
| Photos: [Drop zone or Browse]            |
| [________Submit___________]              |
+------------------------------------------+
```

### 4. Admin Dashboard
```
+------------------------------------------+
| Admin Dashboard      [Bell] [User Avatar]|
+------------------------------------------+
| +----------+ +----------+ +----------+   |
| | Total    | | Pending  | | Resolved |   |
| |   156    | |    42    | |    89    |   |
| +----------+ +----------+ +----------+   |
| +----------+ +----------+ +----------+   |
| |Escalated | | In-Prog  | | Rate     |   |
| |    8     | |    17    | |   57%    |   |
| +----------+ +----------+ +----------+   |
+------------------------------------------+
| Recent Complaints    [View All]          |
+------------------------------------------+
| #ID  | Category | Status | Date | Action |
|------|----------|--------|------|--------|
| #001 | Garbage  | [!]Esc | 3d   | [View] |
| #002 | Road     | [OK]Res| 5d   | [View] |
+------------------------------------------+
```

## Component Structure

### Buttons
```
Primary:  bg-trust-blue text-white rounded-lg px-4 py-2
Secondary: bg-white border text-slate-gray rounded-lg px-4 py-2
Danger:   bg-alert-red text-white rounded-lg px-4 py-2
```

### Status Badges
```
Pending:    bg-caution-orange/20 text-caution-orange
In Progress: bg-engagement-blue/20 text-engagement-blue
Resolved:   bg-growth-green/20 text-growth-green
Escalated:  bg-alert-red/20 text-alert-red
```

### Cards
```
bg-white rounded-lg shadow-md p-4 border border-light-gray
```

### Inputs
```
border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-trust-blue
```

## Responsive Breakpoints
- Mobile: < 640px (stacked layout)
- Tablet: 640px - 1024px (2 columns)
- Desktop: > 1024px (3+ columns)

## Tailwind Config (colors)
```js
colors: {
  'trust-blue': '#2563eb',
  'engagement-blue': '#3b82f6',
  'growth-green': '#10b981',
  'caution-orange': '#f59e0b',
  'alert-red': '#ef4444',
}
```

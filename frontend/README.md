# Gatherly Frontend

A modern, sleek event management platform built with Next.js, TypeScript, and Tailwind CSS.

## 🎨 Brand Identity

**Gatherly** - Where great events come to life

- Modern purple-to-blue gradient design
- Glassmorphism UI effects
- Dark mode interface
- Community-focused branding

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Environment Variables

Create a `.env.local` file (already created):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📦 Tech Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Data Fetching**: SWR
- **Forms**: React Hook Form + Zod
- **Animations**: Framer Motion

## 🎯 Features

### ✅ Completed

- **Authentication**
  - Login page with animated background
  - Signup page with role selection (User/Organizer)
  - JWT token management with auto-refresh
  - Protected routes

- **Dashboard**
  - Welcome screen with user stats
  - Quick actions
  - Getting started guide
  - Upcoming events section

- **Events**
  - Event listing with search
  - Event cards with capacity visualization
  - Pagination
  - Status badges

- **UI Components**
  - Button (4 variants, loading states)
  - Input (with labels, errors)
  - Card (glassmorphism effects)
  - Badge (status-based colors)
  - Spinner
  - Navbar

### 🚧 To Be Implemented

- Event detail page
- Event creation/edit forms
- Task management
- Attendee registration
- Advanced filters
- User profile
- Responsive mobile menu

## 📁 Project Structure

```
frontend/
├── app/
│   ├── dashboard/          # Dashboard pages
│   ├── events/             # Event pages
│   ├── login/              # Login page
│   ├── signup/             # Signup page
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── globals.css         # Global styles
├── components/
│   ├── events/             # Event-specific components
│   │   └── EventCard.tsx
│   ├── layout/             # Layout components
│   │   └── Navbar.tsx
│   └── ui/                 # Reusable UI components
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Card.tsx
│       ├── Badge.tsx
│       └── Spinner.tsx
├── contexts/
│   └── AuthContext.tsx     # Authentication state
├── lib/
│   ├── api.ts              # API client
│   ├── types.ts            # TypeScript interfaces
│   └── utils.ts            # Utility functions
└── public/                 # Static assets
```

## 🎨 Design System

### Colors

- **Primary**: Purple gradient (#7C3AED → #8B5CF6)
- **Accent**: Blue gradient (#3B82F6 → #60A5FA)
- **Background**: Dark navy (#0F172A)
- **Cards**: Dark slate (#1E293B)

### Components

All components follow the Gatherly brand with:
- Glassmorphism effects
- Smooth animations
- Consistent spacing
- Accessible focus states

## 🔐 Authentication Flow

1. User visits the app
2. Redirected to login if not authenticated
3. Login/signup with email and password
4. JWT tokens stored in localStorage
5. Automatic token refresh on expiry
6. Protected routes check authentication

## 📝 Available Scripts

```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 🌐 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`

### Endpoints Used

- `POST /auth/login` - User login
- `POST /auth/signup` - User registration
- `POST /auth/refresh` - Token refresh
- `GET /events` - List events
- `GET /events/{id}` - Get event details
- `POST /events` - Create event (organizers)
- And more...

## 🎯 Next Steps

1. Run `npm install` to install dependencies
2. Start the backend API (`cd .. && uv run fastapi dev`)
3. Start the frontend (`npm run dev`)
4. Visit `http://localhost:3000`
5. Create an account and explore!

## 📸 Screenshots

Login and signup pages feature:
- Animated gradient backgrounds
- Floating orb animations
- Glassmorphism cards
- Smooth transitions

Dashboard includes:
- Stats cards with hover effects
- Quick action buttons
- Getting started guide
- Upcoming events section

Events page shows:
- Grid layout of event cards
- Search functionality
- Capacity visualization
- Status badges

## 🤝 Contributing

This is a personal project for the Behemoth FastAPI event management system.

## 📄 License

MIT License

---

**Built with ❤️ using Next.js and Tailwind CSS**

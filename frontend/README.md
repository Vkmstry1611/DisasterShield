# DisasterShield - React Native App

A React Native app built with Expo Router for disaster management and news verification.

## Setup Instructions

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- Expo CLI

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

### Available Scripts

- `npm start` - Start the Expo development server
- `npm run android` - Run on Android device/emulator
- `npm run ios` - Run on iOS device/simulator
- `npm run web` - Run in web browser

### Project Structure

```
frontend/
├── app/
│   ├── (tabs)/          # Tab navigation screens
│   │   ├── _layout.tsx  # Tab layout configuration
│   │   ├── home.tsx     # Home screen
│   │   ├── news.tsx     # News feed screen
│   │   ├── community.tsx # Community updates
│   │   ├── resources.tsx # Emergency resources
│   │   └── profile.tsx  # User profile
│   ├── _layout.tsx      # Root layout
│   ├── index.tsx        # Entry point
│   └── +not-found.tsx   # 404 page
├── constants/
│   └── colors.ts        # App color scheme
├── mocks/
│   └── newsData.ts      # Mock data for development
└── assets/              # Images and other assets
```

### Features

- **Tab Navigation**: Easy navigation between main app sections
- **News Feed**: Verified and rumor news with AI-powered detection
- **Community Updates**: Real-time community reports
- **Emergency Resources**: Quick access to emergency contacts
- **User Profile**: Authentication and settings

### Dependencies

- **Expo Router**: File-based routing
- **React Native**: Mobile app framework
- **Lucide React Native**: Icon library
- **Expo Haptics**: Haptic feedback
- **TanStack Query**: Data fetching and caching

## Troubleshooting

If you encounter issues:

1. Clear the cache: `npx expo start --clear`
2. Reset Metro bundler: `npx expo start --reset-cache`
3. Reinstall dependencies: `rm -rf node_modules && npm install`

## Development Notes

- The app uses Expo Router for navigation
- Colors are centralized in `constants/colors.ts`
- Mock data is provided for development in `mocks/newsData.ts`
- TypeScript is configured for type safety
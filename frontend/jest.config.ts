import type { Config } from 'jest';
import nextJest from 'next/jest.js'; // Make sure to include .js for ES module imports from CommonJS

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
});

// Add any custom config to be passed to Jest
const customJestConfig: Config = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'], // Changed to .ts assuming setup file will also be TS
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    // Handle CSS imports (if you're not using CSS modules or a specific transformer)
    // '\\.(css|less|scss|sass)$ L: 'identity-obj-proxy', // Example, may not be needed with next/jest

    // Handle module aliases (this will be automatically configured by next/jest when using tsconfig.json paths)
    // However, if you have specific needs, you can add them here.
    // For example, if your tsconfig.json has paths: { "@/components/*": ["src/components/*"] }
    // then next/jest should handle it. If not, you might add:
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  // If you want to collect coverage, uncomment the following lines
  // collectCoverage: true,
  // coverageProvider: 'v8',
  // coverageDirectory: 'coverage',
  // coverageReporters: ['text', 'lcov'],
  // collectCoverageFrom: [
  //   'src/**/*.{js,jsx,ts,tsx}',
  //   '!src/**/*.d.ts',
  //   '!src/**/index.{js,jsx,ts,tsx}', // Often barrel files are excluded
  //   '!src/.*/types/.*' // Exclude type definitions
  // ],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(customJestConfig); 
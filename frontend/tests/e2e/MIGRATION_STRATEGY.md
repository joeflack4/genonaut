# E2E Test Migration Strategy: Mock to Real API

## Overview
This document outlines the strategy for migrating Playwright E2E tests from complex mock patterns to real API testing, based on the comprehensive audit completed in Phase 3.

## Test Categories

### 🟢 **Priority 1: High-Value Real API Migrations**

#### **Gallery Tests** (`gallery.spec.ts`)
- **Status**: Partially migrated (Phase 2 complete)
- **Real API versions**: `gallery-real-api.spec.ts`, `gallery-real-api-improved.spec.ts`
- **Remaining work**:
  - ✅ Basic pagination (`navigates to next page correctly`) - DONE
  - ✅ Content type filtering - DONE
  - ✅ Large dataset pagination (realistic version) - DONE
  - 🔲 Search functionality migration
  - 🔲 Remove deprecated mock patterns

#### **Authentication Tests** (`auth.spec.ts`)
- **Status**: All tests currently skipped due to mock complexity
- **Migration value**: ⭐⭐⭐⭐⭐ CRITICAL
- **Tests to convert**:
  - `redirects logged-in user from login to dashboard`
  - `keeps unauthenticated visitor on signup placeholder`
- **Benefits**: Real session management, proper authentication flow testing

#### **Dashboard Tests** (`dashboard.spec.ts`)
- **Status**: All tests skipped - excellent candidates
- **Migration value**: ⭐⭐⭐⭐⭐ CRITICAL
- **Tests to convert**:
  - `shows gallery stats and recent content`
- **Benefits**: Real data aggregation, actual API statistics

#### **Settings Tests** (`settings.spec.ts`)
- **Status**: All tests skipped - good for CRUD testing
- **Migration value**: ⭐⭐⭐⭐ HIGH
- **Tests to convert**:
  - `persists profile updates and theme preference`
- **Benefits**: Real database updates, state persistence

#### **Recommendations Tests** (`recommendations.spec.ts`)
- **Status**: All tests skipped - ideal for state change testing
- **Migration value**: ⭐⭐⭐⭐ HIGH
- **Tests to convert**:
  - `marks a recommendation as served`
- **Benefits**: Real database state changes, API side effects

### 🔴 **Keep as Mocks: Error & Edge Case Testing**

#### **Error Handling Tests** (`error-handling.spec.ts`)
- **Keep as mocks**: ✅ Perfect use case for mocking
- **Reasons**: Network failures, extreme error conditions, offline scenarios
- **Current issues**: Most tests skipped - need to fix mock patterns
- **Action needed**: Simplify mock patterns, not migrate to real API

#### **Performance Tests** (`performance.spec.ts`)
- **Hybrid approach**: Some real API for realistic performance, mocks for extreme datasets
- **Keep mocked**: Large dataset simulations, memory stress tests
- **Real API candidates**: Basic performance measurements with realistic data

### 🟡 **Working Well: Minimal Changes Needed**

#### **Navigation Tests** (`navigation.spec.ts`)
- **Status**: Working well, keep current approach
- **Reason**: Client-side routing doesn't need API changes

#### **Forms Tests** (`forms.spec.ts`)
- **Status**: Working well, keep current approach
- **Reason**: Form validation is primarily frontend logic

#### **Accessibility Tests** (`accessibility.spec.ts`)
- **Status**: Working well, keep current approach
- **Reason**: ARIA and keyboard navigation are frontend concerns

#### **Theme Tests** (`theme.spec.ts`)
- **Status**: Working well, keep current approach
- **Reason**: Theme switching is client-side state management

#### **Loading/Errors Tests** (`loading-errors.spec.ts`)
- **Status**: Working well, keep current approach
- **Reason**: Basic load testing and error detection

#### **Generation Tests** (`generation.spec.ts`)
- **Status**: Mixed - consider hybrid approach
- **Current**: UI testing works well
- **Potential**: Generation flow could benefit from real API integration

## Migration Priority Queue

### **Phase 3A: Critical Business Logic (Week 1)**
1. **Auth Tests** - Essential for user flows
2. **Dashboard Tests** - Core user experience
3. **Settings Tests** - User profile management

### **Phase 3B: Content Management (Week 2)**
4. **Recommendations Tests** - Content discovery
5. **Gallery Search** - Complete the gallery migration
6. **Generation Tests** - Creation workflows (if applicable)

### **Phase 3C: Cleanup & Optimization (Week 3)**
7. **Error Handling** - Fix mock patterns instead of migrating
8. **Performance** - Hybrid approach implementation
9. **Remove deprecated mocks** - Clean up old gallery mocks

## Technical Implementation Strategy

### **Real API Test Utilities** (Create First)
```typescript
// frontend/tests/e2e/utils/realApiHelpers.ts
export async function waitForRealApiHealth(page: Page): Promise<boolean>
export async function loginAsTestUser(page: Page): Promise<void>
export async function seedTestContent(contentType: string, count: number): Promise<void>
export async function clearTestData(page: Page): Promise<void>
export async function getTestUserId(): Promise<string>
```

### **Migration Pattern**
1. **Create real API version** alongside existing mock test
2. **Add conditional execution** based on real API availability
3. **Test both versions** during transition period
4. **Remove mock version** once real API is stable
5. **Update test runner configuration**

### **Test Data Strategy**
- **Consistent test user**: Use predictable test user ID from seeded data
- **Isolation**: Each test should clean up its own data
- **Realistic data**: Use the 2000+ items from Phase 2 seeding
- **Fast execution**: Minimize database operations per test

## Success Metrics

### **Coverage Goals**
- 90% of skipped tests converted to real API or working mocks
- 100% of authentication flows using real API
- 100% of CRUD operations using real API
- Performance regression: <20% increase in test execution time

### **Quality Gates**
- All migrated tests pass consistently
- No test flakiness introduced
- Real API tests fail gracefully when backend unavailable
- Mock tests simplified and maintainable

## Test Execution Strategy

### **Parallel Execution**
- **Mock tests**: Continue running in parallel with existing CI
- **Real API tests**: Run separately with database setup/teardown
- **Hybrid mode**: Some tests available in both modes during transition

### **CI Integration**
- `make frontend-test-e2e` - Mock-based tests (fast)
- `make frontend-test-e2e-real-api` - Real API tests (comprehensive)
- `make frontend-test-e2e-all` - Run both suites

## Risk Mitigation

### **Common Issues**
1. **Test data contamination**: Implement proper cleanup between tests
2. **Timing issues**: Add proper wait conditions for API responses
3. **Database state**: Use transactions or database reset between tests
4. **Authentication state**: Ensure clean session state per test

### **Rollback Plan**
- Keep original mock tests until real API versions are proven stable
- Feature flags to disable real API tests if issues arise
- Automated fallback to mock tests if real API unavailable

## Current Status: Phase 3 Implementation

✅ **Completed**:
- Comprehensive test audit and categorization
- Identification of skipped tests due to mock complexity
- Migration strategy documentation

🔲 **Next Steps**:
- Create real API test utilities
- Convert authentication tests
- Convert dashboard tests
- Convert settings tests
- Convert recommendations tests
- Run full test suite verification
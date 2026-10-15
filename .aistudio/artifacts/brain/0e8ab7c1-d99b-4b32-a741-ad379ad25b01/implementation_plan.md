# Sheffield Connect — AI Agent, SSO Portal, Role-Tailored Landing & Brand Upgrade

Deliver an intelligent voice- and text-powered AI Action Agent, an authentic Sheffield City Council Microsoft Entra ID Single Sign-On (SSO) experience, role-tailored landing dashboards for each persona, official Sheffield City Council branding, and cleanup of demo sandbox chips.

---

## User Review & Critical Decisions

> [!IMPORTANT]
> The following architectural decisions were confirmed with the user during Phase 1:
>
> 1. **AI Assistant Appearance**: Floating bottom-right assistant widget that can be opened/minimized, displaying both spoken/typed conversation and step-by-step action execution traces in real time.
> 2. **SSO Portal Design**: Authentic Sheffield City Council corporate Microsoft Entra ID / SAML login portal with one-click persona selection, corporate email login, and security policy badges.
> 3. **Voice Input**: Dual input with both real-time voice microphone dictation (Web Speech Recognition API with pulse indicator) and standard text command input in English, Hindi, and Hinglish.
> 4. **Visual Cleanup**: Immediate removal of the orange `SANDBOX DEMO` badge and replacement of the generic icon with the authentic Sheffield City Council logo mark.

---

## 1. Overview & Core Concept

### What It Does
- **Conversational AI Action Agent ("Sheffield Assistant")**: Users can speak or type in natural language (English, Hindi, Hinglish) to execute real actions across the workplace without hunting through menus. The agent understands requests like *"Book 3 days leave for Aisha starting next Monday"*, *"Create a G7 vacancy for Care Coordinator"*, *"Approve Daniel's timesheet"*, or *"Run payroll for 2026-10"*. It executes these actions directly on the reactive data store, showing visual action execution traces, and navigates to the relevant screen with highlighted feedback.
- **Sheffield Council Corporate SSO**: Replaces the generic developer login form with an official Sheffield City Council Single Sign-On portal modelled on Microsoft Entra ID (`sheffield.gov.uk`). Users can select their corporate persona with one click or enter their Sheffield staff email, complete with authentic council heraldry and security declarations.
- **Persona-Specific Landing Dashboards**: Instead of every persona seeing the same generic overview, each role now lands on a purpose-built workspace:
  - **Employee (Aisha Khan)**: Personal Self-Service Hub (Leave balance & upcoming absences, timesheet submission status, assigned learning courses, recent payslip summary, quick absence booker).
  - **Manager (Helen Walker)**: Team Leadership & Approvals Command Centre (Pending team leave requests, pending timesheet reviews, team headcount & FTE breakdown, quick approvals queue).
  - **Recruiter (Grace Turner)**: Talent Acquisition & Pipeline Console (Active requisitions, candidate pipeline stage distributions, interviews awaiting scoring, candidate correspondence inbox).
  - **People Services / HR (Priya Shah)**: Workforce Operations & Governance Hub (New-starter onboarding tracker, confidential HR casework queue, document retention compliance, task SLA monitor).
  - **Payroll Lead (Oliver Reed)**: Payroll Operations & Compliance Centre (Current period calculation status, gross/net variance rollups, payment export queue, payslip publication controls).
  - **Service Director (Matthew Grant)**: Executive Directorate Intelligence (Establishment staffing metrics, cost-centre budget burn, service vacancy rates, workforce distribution).
  - **System Administrator (Sofia Bennett)**: System Health & Integration Console (Mock adapter queue status, retry/fault injection triggers, security audit stream, demo reset controls).
- **Official Sheffield Identity**: Features the authentic Sheffield City Council green & white heraldic arrows and sheaves emblem with official typography, replacing generic blue badges.

---

## 2. User Experience & Visual Design

### Key User Flows

```
┌────────────────────────────────────────────────────────────────────────┐
│             Sheffield City Council Corporate SSO (Entra ID)             │
│  [Official Sheffield Crest] Sheffield City Council Workplace Login     │
│  Quick Persona Selector (Aisha, Helen, Grace, Priya, Oliver, Sofia...) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Instant SSO Auth
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            Role-Tailored Landing Dashboard (Context-Aware)             │
│  • Aisha (Employee)   ──► Employee Self-Service (Leave, Pay, Learning) │
│  • Helen (Manager)    ──► Team Approvals & Spans Command Centre        │
│  • Grace (Recruiter)  ──► Talent Pipeline & Interview Scoring Console  │
│  • Priya (People Svcs)──► HR Operations, Onboarding & Casework         │
│  • Oliver (Payroll)   ──► Payroll Periods & Payment Exports            │
│  • Matthew (Director) ──► Directorate Insights & Cost Center Rollups   │
│  • Sofia (Admin)      ──► Integration Adapters & Audit Console         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌────────────────────────────────────────┐  ┌────────────────────────────────────┐
│      Main Workspace Navigation         │  │   Floating AI Action Assistant     │
│  Strict role-based tabs & capabilities │  │  • Voice mic button (speech-to-text│
│  Clean Topbar without sandbox chip     │  │  • Natural language task input     │
│  Official Sheffield Council Logo       │  │  • Visible Action Execution Trace  │
└────────────────────────────────────────┘  │  • Store mutation & view jump      │
                                            └────────────────────────────────────┘
```

### Visual Identity & Theme
- **Color Palette**:
  - Dominant Neutral: `#FFFFFF` (Surface), `#F4F7FB` (Canvas field), `#122B49` (Deep Navy primary shell).
  - Sheffield Green Brand Accent: `#005A36` (Official Sheffield City Council Heritage Green) with `#E6F4EA` subtle tints.
  - Interactive Action Blue: `#2D77C7` with `#EAF3FD` light highlights.
  - Strict zero-pill discipline: Clean unboxed metadata with `·` separators.
- **Typography**: Manrope for bold display titles (`font-weight: 800`), DM Sans for clear body prose, and monospace tabular numerals (`tabular-nums`) for currency, FTE, and metric counters.
- **Topbar**: Removed the orange `SANDBOX DEMO` box. Retained clean breadcrumbs, user avatar, and refresh trigger.

---

## 3. Key Product Decisions & Trade-Offs

| Decision | Selected Approach | Rationale & Trade-off |
|---|---|---|
| **AI Agent Engine** | Hybrid Natural Language Action Parser & Gemini-powered tool execution | Handles immediate, offline zero-latency execution of all 15+ workplace actions (booking leave, approving items, creating vacancies, assigning tasks) while supporting flexible phrasing in English, Hindi, and Hinglish. |
| **Speech-to-Text Input** | Web Speech Recognition API (`webkitSpeechRecognition`) with visual audio wave pulse | Native browser capability requiring zero external mic streaming latency; gracefully falls back to text input on unsupported devices. |
| **SSO Authenticator** | Microsoft Entra ID simulated corporate login modal with branded Sheffield credentials | Authentic public sector enterprise login aesthetic without requiring live Azure AD tenant binding for offline demonstration. |
| **Persona-Specific Dashboards** | Dynamic component dispatcher based on `user.role` | Ensures immediate distinction between roles; an employee never sees director KPIs on landing, and a manager lands directly on actionable approval queues. |
| **Action Trace Visibility** | Step-by-step visual badge cards inside the AI chat drawer (`Parsing Intent` &rarr; `Validating Rules` &rarr; `Executing Store Mutation` &rarr; `Success`) | Fulfills user requirement that agent tasks are transparently visible in the workflow flow. |

---

## 4. Technical Architecture & Data Strategy

### Component Hierarchy

```
src/
├── App.tsx                     (Root shell, persona state, global toasts & AI assistant)
├── store/
│   ├── sheffieldStore.ts       (Reactive state, role-based queries, 15+ transactional mutations)
│   └── aiAgentService.ts       (Intent parsing, action schemas, natural language speech-to-action)
├── components/
│   ├── AiAssistantWidget.tsx   (Floating drawer, voice mic listener, chat stream, action trace)
│   ├── SheffieldLogo.tsx       (Authentic Sheffield City Council SVG brand mark)
│   ├── Topbar.tsx              (Cleaned header without sandbox chip, Sheffield breadcrumb)
│   ├── Sidebar.tsx             (Role-filtered navigation with Sheffield branding)
│   └── SsoLoginModal.tsx       (Microsoft Entra ID Sheffield City Council SSO login portal)
└── views/
    ├── LoginView.tsx           (Entra ID SSO landing with quick persona cards)
    ├── dashboards/
    │   ├── EmployeeDashboard.tsx (Aisha's personal hub: balances, timesheet, payslips)
    │   ├── ManagerDashboard.tsx  (Helen's team queue: leave approvals, timesheet queue)
    │   ├── RecruiterDashboard.tsx(Grace's talent hub: vacancy pipeline, scoring queue)
    │   ├── HrDashboard.tsx       (Priya's operations hub: onboarding, tasks, cases)
    │   ├── PayrollDashboard.tsx  (Oliver's payroll hub: current period, payslips)
    │   ├── DirectorDashboard.tsx (Matthew's directorate hub: FTE rollups, spend)
    │   └── AdminDashboard.tsx    (Sofia's system console: integrations, audit)
    ├── LeaveView.tsx
    ├── TimesheetsView.tsx
    ├── OrgView.tsx
    ├── RecruitView.tsx
    ├── CandidatePortalView.tsx
    ├── DocumentsView.tsx
    ├── TasksView.tsx
    ├── LearningView.tsx
    ├── PayrollView.tsx
    ├── ReportsView.tsx
    ├── OptionalView.tsx
    ├── IntegrationsView.tsx
    ├── MessagesView.tsx
    ├── GuideView.tsx
    ├── MatrixView.tsx
    └── AuditView.tsx
```

### AI Agent Action Vocabulary & Function Bindings
The AI Assistant will recognize and execute the following intent actions:
1. `book_leave`: Parses leave type, start/end dates, reason; validates weekdays & balance; books leave.
2. `approve_leave` / `reject_leave`: Finds pending leave for team member and executes decision.
3. `submit_timesheet`: Submits weekly hours for current or target employee.
4. `approve_timesheet`: Approves pending timesheet.
5. `create_vacancy`: Extracts title, department, salary, closing date and creates draft vacancy.
6. `publish_vacancy`: Publishes draft vacancy.
7. `assign_task`: Assigns onboarding or HR check task to user.
8. `complete_task`: Marks assigned task complete.
9. `enrol_course`: Books course seat for current user.
10. `submit_expense`: Records expense claim with amount and category.
11. `approve_expense`: Reviews and approves expense.
12. `run_payroll`: Calculates current monthly payroll run.
13. `finalise_payroll`: Finalises payroll run and publishes payslips.
14. `switch_persona`: Instantly switches active role (e.g., "Switch to Helen" or "Helen ke persona me jao").
15. `navigate`: Jumps directly to any workspace view.

---

## 5. Verification & Pre-Flight Plan
1. **Compilation**: Run `compile_applet` to ensure pristine TypeScript build.
2. **SSO Flow Verification**: Test login with persona quick selector and corporate credentials.
3. **Persona-Specific Landing Test**: Confirm Aisha, Helen, Grace, Priya, Oliver, Matthew, and Sofia each see their customized landing dashboard.
4. **AI Agent Voice & Flow Test**: Test voice dictation and text prompts in English and Hindi/Hinglish (e.g. "Aisha ke liye 2 din ki leave book kro"), verifying visible action trace steps and state change.
5. **Brand & Topbar Polish**: Verify Sheffield Council official green & white logo and confirm the orange sandbox chip is completely removed.

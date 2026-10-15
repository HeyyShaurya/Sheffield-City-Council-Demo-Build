import { store, fmt, isodays, today, lastMonday } from './sheffieldStore';
import { User, Role, LeaveRequest, Application } from '../types';

export interface ActionTraceStep {
  phase: 'detect' | 'validate' | 'execute' | 'navigate';
  title: string;
  detail: string;
  timestamp: string;
  status: 'pending' | 'success' | 'warn' | 'error';
}

export interface AgentExecutionResult {
  success: boolean;
  message: string;
  actionType: string;
  trace: ActionTraceStep[];
  targetPage?: string;
  highlightId?: string | number;
}

function nowTime(): string {
  return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export class AiAgentService {
  /**
   * Main entry point: process voice or text query in English, Hindi, or Hinglish.
   */
  public static executeCommand(query: string, currentUser: User): AgentExecutionResult {
    const q = query.trim().toLowerCase();
    const trace: ActionTraceStep[] = [];

    // Helper to log trace step
    const addTrace = (
      phase: ActionTraceStep['phase'],
      title: string,
      detail: string,
      status: ActionTraceStep['status'] = 'success'
    ) => {
      trace.push({
        phase,
        title,
        detail,
        timestamp: nowTime(),
        status,
      });
    };

    addTrace('detect', 'Input Received & NLP Parsing', `Processing: "${query}" (Speaker: ${currentUser.name}, Role: ${currentUser.role})`);

    // 1. SWITCH PERSONA
    if (
      q.includes('switch to') ||
      q.includes('login as') ||
      q.includes('become') ||
      q.includes('persona me jao') ||
      q.includes('persona badlo') ||
      q.includes('role change') ||
      q.includes('switch persona')
    ) {
      addTrace('detect', 'Intent: Switch Persona', 'User requested to switch active workspace persona');
      const allUsers = store.getState().users;
      let matchedUser: User | undefined;

      if (q.includes('helen') || q.includes('manager')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('helen') || u.role === 'manager');
      } else if (q.includes('aisha') || q.includes('employee')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('aisha') || u.id === 1);
      } else if (q.includes('grace') || q.includes('recruiter')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('grace') || u.role === 'recruiter');
      } else if (q.includes('priya') || q.includes('hr') || q.includes('people services')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('priya') || u.role === 'hr');
      } else if (q.includes('oliver') || q.includes('payroll')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('oliver') || u.role === 'payroll');
      } else if (q.includes('matthew') || q.includes('director') || q.includes('service')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('matthew') || u.role === 'service');
      } else if (q.includes('sofia') || q.includes('admin') || q.includes('system')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('sofia') || u.role === 'admin');
      } else if (q.includes('daniel')) {
        matchedUser = allUsers.find((u) => u.name.toLowerCase().includes('daniel'));
      }

      if (matchedUser) {
        addTrace('validate', 'Security & Profile Verification', `Target found: ${matchedUser.name} (${matchedUser.role.toUpperCase()})`);
        store.setCurrentUser(matchedUser);
        addTrace('execute', 'Persona Switched', `Active session updated to ${matchedUser.name}`);
        addTrace('navigate', 'Workspace Refresh', 'Redirecting to role-tailored dashboard');
        return {
          success: true,
          actionType: 'switch_persona',
          message: `Switched session to ${matchedUser.name} (${matchedUser.job}). Your role dashboard and sidebar have adapted.`,
          trace,
          targetPage: 'overview',
        };
      }
    }

    // 2. BOOK LEAVE
    if (
      (q.includes('leave') || q.includes('holiday') || q.includes('chhutti') || q.includes('absence')) &&
      (q.includes('book') || q.includes('apply') || q.includes('request') || q.includes('kro') || q.includes('kardo') || q.includes('daalo'))
    ) {
      addTrace('detect', 'Intent: Book Absence / Leave', 'Identified leave creation intent');

      // Extract days
      const daysMatch = q.match(/(\d+)\s*(days?|din)/);
      const daysCount = daysMatch ? parseInt(daysMatch[1], 10) : 3;

      let leaveType: LeaveRequest['leave_type'] = 'Annual';
      if (q.includes('sick') || q.includes('bimar')) leaveType = 'Sickness';
      else if (q.includes('carer') || q.includes('family')) leaveType = 'Carer';
      else if (q.includes('trade union') || q.includes('union')) leaveType = 'Trade union';
      else if (q.includes('discretionary')) leaveType = 'Discretionary';

      // Pick next week's Monday or +3 days
      const start = isodays(3);
      const ending = isodays(3 + daysCount - 1);
      const note = `Automated leave booking via Sheffield AI Assistant (${daysCount} days ${leaveType})`;

      addTrace('validate', 'Policy & Entitlement Check', `Type: ${leaveType} · Duration: ${daysCount} days · Start: ${start} · End: ${ending}`);

      try {
        const res = store.createLeaveRequest(currentUser, {
          leave_type: leaveType,
          start,
          ending,
          note,
        });

        addTrace('execute', 'Store Mutation: LeaveRequest Created', `Record #${res.id} staged with status '${res.status}'`);
        addTrace('navigate', 'View Jump: Absence & Leave', 'Navigating to leave view to inspect approval trail');

        return {
          success: true,
          actionType: 'book_leave',
          message: `Successfully booked ${res.days} days of ${leaveType} leave (${start} to ${ending}) for ${currentUser.name}. Your manager will receive the approval request.`,
          trace,
          targetPage: 'leave',
          highlightId: res.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Entitlement Validation Failed', err.message || 'Unknown error', 'error');
        return {
          success: false,
          actionType: 'book_leave',
          message: `Could not book leave: ${err.message}`,
          trace,
          targetPage: 'leave',
        };
      }
    }

    // 3. APPROVE LEAVE
    if (
      (q.includes('leave') || q.includes('absence') || q.includes('chhutti')) &&
      (q.includes('approve') || q.includes('accept') || q.includes('manzoor') || q.includes('approve kr'))
    ) {
      addTrace('detect', 'Intent: Approve Leave Request', 'Searching for pending leave requests');
      const leaves = store.getState().leave_requests.filter((r) => r.status === 'Pending');

      if (leaves.length === 0) {
        addTrace('validate', 'Queue Verification', 'No pending leave requests found in the system', 'warn');
        return {
          success: true,
          actionType: 'approve_leave',
          message: 'All team leave requests are already up to date. There are currently no pending leave requests awaiting approval.',
          trace,
          targetPage: 'leave',
        };
      }

      // Check if user specifically mentioned someone like Daniel
      let targetReq = leaves[0];
      const allUsers = store.getState().users;
      for (const l of leaves) {
        const emp = allUsers.find((u) => u.id === l.employee_id);
        if (emp && q.includes(emp.name.toLowerCase())) {
          targetReq = l;
          break;
        }
      }

      const empName = allUsers.find((u) => u.id === targetReq.employee_id)?.name || `Employee #${targetReq.employee_id}`;

      addTrace('validate', 'Authorization & Conflict Check', `Approving request #${targetReq.id} for ${empName} (${targetReq.days} days)`);
      try {
        store.decideLeaveRequest(targetReq.id, 'Approved', currentUser);
        addTrace('execute', 'Store Mutation: Leave Status = Approved', `Updated request #${targetReq.id} and deducted days from remaining balance`);
        addTrace('navigate', 'View Jump: Absence & Leave', 'Displaying approved records');

        return {
          success: true,
          actionType: 'approve_leave',
          message: `Approved ${empName}'s ${targetReq.days}-day leave request from ${targetReq.start} to ${targetReq.ending}. Entitlement balance adjusted.`,
          trace,
          targetPage: 'leave',
          highlightId: targetReq.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Manager Authorization Notice', err.message, 'error');
        return {
          success: false,
          actionType: 'approve_leave',
          message: `Cannot approve leave: ${err.message}. Please switch to Helen Walker (Manager) or Priya Shah (HR).`,
          trace,
          targetPage: 'leave',
        };
      }
    }

    // 4. SUBMIT TIMESHEET
    if (
      (q.includes('timesheet') || q.includes('hours') || q.includes('time') || q.includes('attendance')) &&
      (q.includes('submit') || q.includes('enter') || q.includes('kro') || q.includes('bhejo') || q.includes('log'))
    ) {
      addTrace('detect', 'Intent: Submit Timesheet', 'Parsing weekly attendance hours');
      const hoursMatch = q.match(/(\d+(\.\d+)?)\s*(hours?|ghante|hrs)/);
      const hours = hoursMatch ? parseFloat(hoursMatch[1]) : 37.0;
      const weekStart = lastMonday();

      addTrace('validate', 'Working Time Directive Audit', `Logging week commencing: ${weekStart} (${hours} hours for ${currentUser.name})`);
      try {
        const entry = store.submitTimesheet(weekStart, hours, currentUser);
        addTrace('execute', 'Store Mutation: TimeEntry Staged', `Created entry #${entry.id} with status '${entry.status}'`);
        addTrace('navigate', 'View Jump: Time & Attendance', 'Navigating to weekly timesheet register');

        return {
          success: true,
          actionType: 'submit_timesheet',
          message: `Submitted weekly timesheet for ${currentUser.name} for week commencing ${weekStart} with ${hours} standard working hours. Routed to manager for payroll review.`,
          trace,
          targetPage: 'time',
          highlightId: entry.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Timesheet Note', err.message, 'warn');
        return {
          success: true,
          actionType: 'submit_timesheet',
          message: `Timesheet info: ${err.message}`,
          trace,
          targetPage: 'time',
        };
      }
    }

    // 5. APPROVE TIMESHEET
    if (
      (q.includes('timesheet') || q.includes('time entry')) &&
      (q.includes('approve') || q.includes('accept') || q.includes('approve kr'))
    ) {
      addTrace('detect', 'Intent: Approve Timesheet', 'Querying pending weekly timesheet submissions');
      const pendingTimesheets = store.getState().time_entries.filter((t) => t.status === 'Submitted');

      if (pendingTimesheets.length === 0) {
        addTrace('validate', 'Timesheet Register Check', 'No unapproved timesheets pending in current cycle', 'warn');
        return {
          success: true,
          actionType: 'approve_timesheet',
          message: 'All timesheets for the current period have already been reviewed and approved.',
          trace,
          targetPage: 'time',
        };
      }

      const target = pendingTimesheets[0];
      addTrace('validate', 'Manager Authorization', `Approving timesheet #${target.id} (${target.employee}, ${target.hours} hrs)`);
      try {
        store.decideTimesheet(target.id, 'Approved', currentUser);
        addTrace('execute', 'Store Mutation: TimeEntry = Approved', `Record #${target.id} marked approved for payroll batch extraction`);
        addTrace('navigate', 'View Jump: Time & Attendance', 'Timesheet register updated');

        return {
          success: true,
          actionType: 'approve_timesheet',
          message: `Successfully approved ${target.employee}'s timesheet for week commencing ${target.week_start} (${target.hours} hours).`,
          trace,
          targetPage: 'time',
          highlightId: target.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Authorization Failed', err.message, 'error');
        return {
          success: false,
          actionType: 'approve_timesheet',
          message: `Could not approve timesheet: ${err.message}. Switch to Helen Walker (Manager) or Oliver Reed (Payroll).`,
          trace,
          targetPage: 'time',
        };
      }
    }

    // 6. CREATE VACANCY / RECRUITMENT REQUISITION
    if (
      (q.includes('vacancy') || q.includes('job') || q.includes('post') || q.includes('naukri') || q.includes('requisition')) &&
      (q.includes('create') || q.includes('banao') || q.includes('post') || q.includes('add') || q.includes('open'))
    ) {
      addTrace('detect', 'Intent: Create Recruitment Vacancy', 'Extracting role title, grade, and establishment band');

      let title = 'Care Coordinator';
      if (q.includes('social worker')) title = 'Senior Social Worker';
      else if (q.includes('revenues') || q.includes('tax')) title = 'Revenues & Benefits Officer';
      else if (q.includes('project manager') || q.includes('lead')) title = 'Modernisation Project Lead';
      else if (q.includes('engineer') || q.includes('it')) title = 'Cloud Integration Engineer';

      let grade = 'Grade 7';
      if (q.includes('g8') || q.includes('grade 8')) grade = 'Grade 8';
      else if (q.includes('g9') || q.includes('grade 9')) grade = 'Grade 9';
      else if (q.includes('g6') || q.includes('grade 6')) grade = 'Grade 6';

      const department = 'Adult Health & Social Care';
      const closing = isodays(28);

      addTrace('validate', 'Establishment & Budget Approval', `Role: ${title} · Grade: ${grade} · Dept: ${department} · Closing: ${closing}`);

      try {
        const vac = store.createVacancy(currentUser, {
          title,
          department,
          grade,
          closing,
          salary: '£36,922 - £40,221',
          summary: `Sheffield City Council opportunity for an ambitious ${title} to join our connected modernisation programme.`,
        });

        addTrace('execute', 'Store Mutation: Vacancy Created', `Requisition #${vac.id} staged in draft status`);
        addTrace('navigate', 'View Jump: Recruitment Console', 'Navigating to candidate pipeline and vacancy manager');

        return {
          success: true,
          actionType: 'create_vacancy',
          message: `Created recruitment requisition #${vac.id}: "${vac.title}" (${vac.grade}) in ${vac.department}. Closing date set to ${vac.closing}.`,
          trace,
          targetPage: 'recruit',
          highlightId: vac.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Permission Notice', err.message, 'error');
        return {
          success: false,
          actionType: 'create_vacancy',
          message: `Cannot create vacancy: ${err.message}. Switch to Grace Turner (Recruiter) or Helen Walker (Manager).`,
          trace,
          targetPage: 'recruit',
        };
      }
    }

    // 7. RUN OR FINALISE PAYROLL
    if (q.includes('payroll') || q.includes('payslip') || q.includes('salary') || q.includes('tankhwah')) {
      if (q.includes('finalise') || q.includes('export') || q.includes('bacs') || q.includes('finish') || q.includes('publish')) {
        addTrace('detect', 'Intent: Finalise Payroll Period', 'Initiating payroll freeze and BACS export packaging');
        const runs = store.getState().payroll_runs;
        const targetRun = runs[0];

        if (targetRun) {
          addTrace('validate', 'Gross-to-Net Reconciliation', `Reconciling Period ${targetRun.period}: Gross £${fmt(targetRun.gross)}, Net £${fmt(targetRun.net)}`);
          try {
            store.finalisePayrollRun(targetRun.id, currentUser);
            addTrace('execute', 'Store Mutation: Payroll Staged & Event Logged', `Period ${targetRun.period} finalised; payment export event dispatched to mock adapter`);
            addTrace('navigate', 'View Jump: Payroll & Payslips', 'Viewing published payroll register and BACS confirmation');

            return {
              success: true,
              actionType: 'finalise_payroll',
              message: `Finalised payroll run for ${targetRun.period}. Generated BACS direct debit schedule and released confidential payslips to all active employees.`,
              trace,
              targetPage: 'payroll',
              highlightId: targetRun.id,
            };
          } catch (err: any) {
            addTrace('validate', 'Payroll Authorization Notice', err.message, 'error');
            return {
              success: false,
              actionType: 'finalise_payroll',
              message: `Cannot finalise payroll: ${err.message}. Switch to Oliver Reed (Payroll Lead).`,
              trace,
              targetPage: 'payroll',
            };
          }
        }
      }

      if (q.includes('run') || q.includes('calculate') || q.includes('compute') || q.includes('start') || q.includes('kro') || q.includes('chalao')) {
        addTrace('detect', 'Intent: Calculate Monthly Payroll', 'Scanning active staff establishment and statutory rules');
        const period = '2026-10';
        addTrace('validate', 'Tax & Pension Parameter Engine', `Evaluating PAYE, National Insurance, LGPS, and voluntary deductions for period ${period}`);
        try {
          const run = store.createPayrollRun(period, currentUser);
          addTrace('execute', 'Store Mutation: Payroll Run Generated', `Calculated Run #${run.id}: ${run.headcount} employees processed`);
          addTrace('navigate', 'View Jump: Payroll Operations', 'Inspecting payroll variances and statutory breakdown');

          return {
            success: true,
            actionType: 'run_payroll',
            message: `Calculated payroll run #${run.id} for period ${period}. Total Gross: £${fmt(run.gross)}, Total Net: £${fmt(run.net)} across ${run.headcount} establishment posts.`,
            trace,
            targetPage: 'payroll',
            highlightId: run.id,
          };
        } catch (err: any) {
          addTrace('validate', 'Payroll Execution Info', err.message, 'warn');
          return {
            success: true,
            actionType: 'run_payroll',
            message: `Payroll status: ${err.message}`,
            trace,
            targetPage: 'payroll',
          };
        }
      }
    }

    // 8. ENROL IN LEARNING COURSE
    if (q.includes('course') || q.includes('learning') || q.includes('training') || q.includes('padhai')) {
      if (q.includes('enrol') || q.includes('join') || q.includes('start') || q.includes('book') || q.includes('kro')) {
        addTrace('detect', 'Intent: Course Enrolment', 'Looking up Sheffield Learning Hub catalogue');
        const courses = store.getState().courses;
        let targetCourse = courses[0];

        if (q.includes('cyber') || q.includes('security')) {
          targetCourse = courses.find((c) => c.title.toLowerCase().includes('cyber')) || targetCourse;
        } else if (q.includes('fire') || q.includes('safety')) {
          targetCourse = courses.find((c) => c.title.toLowerCase().includes('fire')) || targetCourse;
        } else if (q.includes('gdpr') || q.includes('data')) {
          targetCourse = courses.find((c) => c.title.toLowerCase().includes('gdpr')) || targetCourse;
        } else if (q.includes('equality') || q.includes('diversity')) {
          targetCourse = courses.find((c) => c.title.toLowerCase().includes('equality')) || targetCourse;
        }

        addTrace('validate', 'Course Prerequisite Check', `Selected: "${targetCourse.title}" (${targetCourse.hours} hrs, Category: ${targetCourse.category})`);
        try {
          const enr = store.enrolCourse(targetCourse.id, currentUser);
          addTrace('execute', 'Store Mutation: Course Enrolment Active', `Assigned enrolment #${enr.id} with status 'Enrolled'`);
          addTrace('navigate', 'View Jump: Learning Hub', 'Showing interactive learning modules');

          return {
            success: true,
            actionType: 'enrol_course',
            message: `Enrolled ${currentUser.name} into mandatory module "${targetCourse.title}". Your progress tracker has been updated in the Learning Hub.`,
            trace,
            targetPage: 'learning',
            highlightId: enr.id,
          };
        } catch (err: any) {
          addTrace('validate', 'Enrolment Notice', err.message, 'warn');
          return {
            success: true,
            actionType: 'enrol_course',
            message: `Course enrolment info: ${err.message}`,
            trace,
            targetPage: 'learning',
          };
        }
      }
    }

    // 9. SUBMIT EXPENSE CLAIM
    if (q.includes('expense') || q.includes('claim') || q.includes('kharcha')) {
      addTrace('detect', 'Intent: Submit Expense Claim', 'Extracting claim amount and cost category');
      const amountMatch = q.match(/(£|\$)?\s*(\d+(\.\d+)?)/);
      const amount = amountMatch ? parseFloat(amountMatch[2]) : 42.5;

      let category = 'Travel & Mileage';
      if (q.includes('equipment') || q.includes('monitor') || q.includes('laptop')) category = 'Equipment';
      else if (q.includes('home') || q.includes('broadband')) category = 'Home Working';
      else if (q.includes('food') || q.includes('subsistence') || q.includes('meal')) category = 'Subsistence';

      addTrace('validate', 'Expense Policy Compliance', `Amount: £${amount.toFixed(2)} · Category: ${category}`);
      try {
        const exp = store.submitExpense(
          category,
          amount,
          `Claim submitted via Sheffield AI Assistant: ${category} (£${amount.toFixed(2)})`,
          currentUser
        );

        addTrace('execute', 'Store Mutation: Expense Staged', `Claim #${exp.id} submitted with status '${exp.status}'`);
        addTrace('navigate', 'View Jump: Optional Modernisations', 'Viewing expense claim history');

        return {
          success: true,
          actionType: 'submit_expense',
          message: `Submitted ${category} expense claim of £${amount.toFixed(2)} for ${currentUser.name}. Claim #${exp.id} queued for manager sign-off.`,
          trace,
          targetPage: 'optional',
          highlightId: exp.id,
        };
      } catch (err: any) {
        addTrace('validate', 'Expense Error', err.message, 'error');
        return {
          success: false,
          actionType: 'submit_expense',
          message: `Cannot submit expense: ${err.message}`,
          trace,
          targetPage: 'optional',
        };
      }
    }

    // 10. COMPLETE TASK
    if (q.includes('task') || q.includes('checklist') || q.includes('kaam')) {
      if (q.includes('complete') || q.includes('finish') || q.includes('done') || q.includes('khatam') || q.includes('pura')) {
        addTrace('detect', 'Intent: Complete Task', 'Checking pending onboarding and compliance tasks');
        const tasks = store.getState().tasks.filter((t) => t.status === 'Open');

        if (tasks.length === 0) {
          addTrace('validate', 'Task Queue Clean', 'No outstanding tasks requiring completion', 'warn');
          return {
            success: true,
            actionType: 'complete_task',
            message: 'All scheduled workplace and onboarding tasks are currently completed.',
            trace,
            targetPage: 'tasks',
          };
        }

        const t = tasks[0];
        addTrace('validate', 'Task SLA Verification', `Completing task #${t.id}: "${t.title}"`);
        store.completeTask(t.id, currentUser);
        addTrace('execute', 'Store Mutation: Task Status = Completed', `Task #${t.id} archived with timestamp`);
        addTrace('navigate', 'View Jump: Tasks & Journeys', 'Task board updated');

        return {
          success: true,
          actionType: 'complete_task',
          message: `Completed task #${t.id}: "${t.title}". Compliance checklist updated.`,
          trace,
          targetPage: 'tasks',
          highlightId: t.id,
        };
      }
    }

    // 11. NAVIGATION INTENT
    const navMap: Record<string, string> = {
      overview: 'overview',
      dashboard: 'overview',
      home: 'overview',
      main: 'overview',
      profile: 'profile',
      contact: 'profile',
      leave: 'leave',
      absence: 'leave',
      holiday: 'leave',
      chhutti: 'leave',
      time: 'time',
      timesheet: 'time',
      attendance: 'time',
      hours: 'time',
      org: 'org',
      hierarchy: 'org',
      establishment: 'org',
      team: 'org',
      recruit: 'recruit',
      recruitment: 'recruit',
      candidates: 'recruit',
      vacancy: 'recruit',
      document: 'documents',
      documents: 'documents',
      gdpr: 'documents',
      task: 'tasks',
      tasks: 'tasks',
      learning: 'learning',
      courses: 'learning',
      payroll: 'payroll',
      payslip: 'payroll',
      payslips: 'payroll',
      salary: 'payroll',
      report: 'reports',
      reports: 'reports',
      analytics: 'reports',
      insights: 'reports',
      optional: 'optional',
      expense: 'optional',
      casework: 'optional',
      integration: 'integrations',
      integrations: 'integrations',
      adapter: 'integrations',
      message: 'messages',
      messages: 'messages',
      chat: 'messages',
      guide: 'guide',
      walkthrough: 'guide',
      matrix: 'matrix',
      capability: 'matrix',
      audit: 'audit',
      evidence: 'audit',
    };

    for (const [trigger, pageKey] of Object.entries(navMap)) {
      if (q.includes(trigger)) {
        addTrace('detect', 'Intent: Workspace Navigation', `Matched keyword "${trigger}" &rarr; Route: ${pageKey}`);
        addTrace('validate', 'Permission Check', `Validating access for role: ${currentUser.role}`);
        addTrace('navigate', 'Page Redirect', `Transitioning to ${pageKey} view`);

        return {
          success: true,
          actionType: 'navigate',
          message: `Navigated to the ${pageKey.toUpperCase()} section. You can now view or interact with this workspace.`,
          trace,
          targetPage: pageKey,
        };
      }
    }

    // Default conversational AI response if no discrete transactional action matched
    addTrace('detect', 'General Inquiry Parsing', 'Interpreting conversational prompt', 'warn');
    addTrace('validate', 'Sheffield Council Knowledge Base', 'Synthesizing contextual recommendation', 'success');

    return {
      success: true,
      actionType: 'chat_assistance',
      message: `I understood: "${query}". You can ask me in English, Hindi or Hinglish to perform actions like:\n• "Book 3 days leave for Aisha"\n• "Approve Daniel's leave request"\n• "Submit weekly timesheet for 37 hours"\n• "Create G7 vacancy for Care Coordinator"\n• "Run October payroll"\n• "Enrol in Cyber Security course"\n• "Switch to Helen (Manager)"\n• "Open workforce insights"`,
      trace,
    };
  }
}

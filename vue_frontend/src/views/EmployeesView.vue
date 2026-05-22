<template>
  <div class="page-wrapper">
    <!-- Page header -->
    <div class="page-header">
      <div class="header-left">
        <div class="breadcrumb">
          <button class="btn-text" style="padding:0" @click="$router.push('/companies')">Companies</button>
          <span class="separator">/</span>
          <span>{{ companyName || 'Company' }}</span>
        </div>
        <h1 class="page-title">Employees</h1>
      </div>
      <div class="flex items-center gap-2">
        <button @click="downloadTemplate" class="btn-light">CSV Template</button>
        <button @click="showImportModal = true" class="btn-secondary">Import CSV</button>
        <button @click="openCreate" class="btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Employee
        </button>
      </div>
    </div>

    <!-- Active / Archived toggle -->
    <div class="view-toggle">
      <button @click="setView('active')" class="toggle-btn" :class="{ active: viewMode === 'active' }">
        Active <span class="count-chip">{{ activeEmployees.length }}</span>
      </button>
      <button @click="setView('archived')" class="toggle-btn" :class="{ active: viewMode === 'archived' }">
        Archived <span class="count-chip">{{ archivedEmployees.length }}</span>
      </button>
    </div>

    <!-- Employee table -->
    <div class="card" style="padding:0; overflow:hidden;">
      <table class="data-table">
        <thead>
          <tr>
            <th>First Names</th>
            <th>Last Name</th>
            <th>Employee #</th>
            <th>Position</th>
            <th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="emp in visibleEmployees" :key="emp.id" :class="{ 'row-archived': !emp.is_active }">
            <td class="font-medium">{{ emp.first_names }}</td>
            <td>{{ emp.last_name }}</td>
            <td>{{ emp.employee_no || '—' }}</td>
            <td>{{ emp.position || '—' }}</td>
            <td>
              <div class="actions" style="justify-content:flex-end">
                <template v-if="emp.is_active">
                  <button @click="openEdit(emp)" class="btn-secondary">Edit</button>
                  <button @click="openLeave(emp)" class="btn-light">Leave</button>
                  <button @click="confirmArchive(emp)" class="btn-text danger">Archive</button>
                </template>
                <template v-else>
                  <span class="badge-archived">Archived</span>
                  <button @click="restore(emp)" class="btn-secondary">Restore</button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="visibleEmployees.length === 0" class="empty-state">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
        <p>{{ viewMode === 'archived' ? 'No archived employees.' : 'No employees yet. Add your first employee.' }}</p>
      </div>
    </div>

    <!-- Archive confirmation modal -->
    <div v-if="archiveTarget" class="modal-overlay" style="z-index:600" @click.self="archiveTarget = null">
      <div class="modal" style="max-width:440px">
        <div class="modal-header">
          <h2>Archive employee?</h2>
          <button @click="archiveTarget = null" class="modal-close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p class="archive-name">{{ archiveTarget.first_names }} {{ archiveTarget.last_name }}</p>
          <p class="archive-detail">Archiving this employee will:</p>
          <ul class="archive-list">
            <li>Remove them from all future payroll runs</li>
            <li>Disable their portal login (if they have one)</li>
            <li>Preserve all historical payslips and audit records</li>
          </ul>
          <p class="archive-restore-note">You can restore them at any time from the Archived tab.</p>
        </div>
        <div class="modal-footer">
          <button @click="archiveTarget = null" class="btn-secondary">Cancel</button>
          <button @click="doArchive" :disabled="archiving" class="btn-danger">
            {{ archiving ? 'Archiving…' : 'Archive employee' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ───── Employee Drawer ───── -->
    <Transition name="drawer-backdrop">
      <div v-if="showDrawer" class="drawer-backdrop" @click.self="close" />
    </Transition>

    <Transition name="drawer-slide">
      <div v-if="showDrawer" class="drawer" role="dialog" aria-modal="true">

        <!-- Drawer header -->
        <div class="drawer-header">
          <div>
            <h2 class="drawer-title">{{ editing ? 'Edit Employee' : 'New Employee' }}</h2>
            <p class="drawer-subtitle" v-if="editing">{{ editing.first_names }} {{ editing.last_name }}</p>
          </div>
          <button class="modal-close" @click="close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Drawer tabs -->
        <div class="drawer-tabs">
          <button
            v-for="tab in TABS" :key="tab.id"
            class="drawer-tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >{{ tab.label }}</button>
        </div>

        <!-- Drawer body (scrollable) -->
        <div class="drawer-body">

          <!-- ── Personal Info tab ── -->
          <div v-if="activeTab === 'personal'" class="tab-content fade-in">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">First Names <span class="req">*</span></label>
                <input v-model="form.first_names" type="text" class="form-input" placeholder="Jane" />
              </div>
              <div class="form-group">
                <label class="form-label">Last Name <span class="req">*</span></label>
                <input v-model="form.last_name" type="text" class="form-input" placeholder="Doe" />
              </div>
              <div class="form-group">
                <label class="form-label">Employee #</label>
                <input v-model="form.employee_no" type="text" class="form-input" placeholder="EMP001" />
              </div>
              <div class="form-group">
                <label class="form-label">ID / Passport</label>
                <input v-model="form.id_no" type="text" class="form-input" placeholder="9001010001088" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Position / Job Title</label>
                <input v-model="form.position" type="text" class="form-input" placeholder="Software Developer" />
              </div>
              <div class="form-group">
                <label class="form-label">Employment Date</label>
                <input v-model="form.emp_date" type="date" class="form-input" />
              </div>
              <div class="form-group" style="display:flex;align-items:center;gap:10px;padding-top:20px">
                <label class="toggle-switch">
                  <input type="checkbox" v-model="form.is_active" />
                  <span class="toggle-track"><span class="toggle-thumb"/></span>
                </label>
                <span style="font-size:13px;font-weight:500;color:var(--color-text-base)">Active</span>
              </div>
            </div>
          </div>

          <!-- ── Banking tab ── -->
          <div v-if="activeTab === 'banking'" class="tab-content fade-in">
            <div class="info-box info-blue" style="margin-bottom:16px">
              Banking details are used for EFT payroll batch files.
            </div>
            <div class="form-grid">
              <div class="form-group span-2">
                <label class="form-label">Bank Name</label>
                <input v-model="form.bank_name" type="text" class="form-input" placeholder="e.g. Standard Bank" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Account Number</label>
                <input v-model="form.account_number" type="text" class="form-input" placeholder="123456789" />
              </div>
              <div class="form-group">
                <label class="form-label">Branch Code</label>
                <input v-model="form.branch_code" type="text" class="form-input" placeholder="051001" />
              </div>
              <div class="form-group">
                <label class="form-label">Account Type</label>
                <select v-model="form.account_type" class="form-input">
                  <option value="">Select type</option>
                  <option value="current">Current / Cheque</option>
                  <option value="savings">Savings</option>
                  <option value="transmission">Transmission</option>
                </select>
              </div>
            </div>
          </div>

          <!-- ── Salary & Deductions tab ── -->
          <div v-if="activeTab === 'salary'" class="tab-content fade-in">

            <!-- Calculation mode -->
            <div class="section-block">
              <div class="section-block-header">
                <span class="section-block-title">Calculation Mode</span>
                <div class="calc-mode-toggle">
                  <span :class="{ 'mode-active': calcMode === 'normal' }">Normal</span>
                  <label class="toggle-switch">
                    <input type="checkbox" v-model="reverseToggle" @change="calcMode = reverseToggle ? 'reverse' : 'normal'" />
                    <span class="toggle-track"><span class="toggle-thumb"/></span>
                  </label>
                  <span :class="{ 'mode-active': calcMode === 'reverse' }">Reverse</span>
                </div>
              </div>
              <div v-if="calcMode === 'reverse'" class="form-grid" style="margin-top:12px">
                <div class="form-group">
                  <label class="form-label">Target Net Pay</label>
                  <input v-model.number="targetNetPay" type="number" min="0" step="0.01" class="form-input" />
                </div>
                <div class="form-group" style="justify-content:flex-end;padding-bottom:4px">
                  <span style="font-size:12px;color:var(--color-text-muted)">Compute gross from desired net</span>
                </div>
              </div>
            </div>

            <!-- Earnings -->
            <div class="section-block">
              <div class="section-block-title" style="margin-bottom:12px">Earnings (Monthly)</div>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Basic Pay</label>
                  <input v-model.number="form.basic_salary" type="number" min="0" step="0.01" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Other Earnings</label>
                  <input v-model.number="form.other_allowances" type="number" min="0" step="0.01" class="form-input" />
                </div>
              </div>
            </div>

            <!-- Deductions -->
            <div class="section-block">
              <div class="section-block-title" style="margin-bottom:12px">Deductions (Monthly)</div>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Pension / Retirement</label>
                  <input v-model.number="form.pension_contribution" type="number" min="0" step="0.01" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Medical Aid</label>
                  <input v-model.number="form.medical_aid" type="number" min="0" step="0.01" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Union Fees</label>
                  <input v-model.number="form.union_fees" type="number" min="0" step="0.01" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Other Deductions</label>
                  <input v-model.number="form.other_deductions" type="number" min="0" step="0.01" class="form-input" />
                </div>
              </div>
            </div>

            <!-- SDL -->
            <div class="section-block">
              <div class="section-block-title" style="margin-bottom:12px">Skills Development Levy (SDL)</div>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Annual Payroll</label>
                  <input v-model.number="sdl.annual_payroll" type="number" min="0" step="0.01" class="form-input" />
                  <span style="font-size:11px;color:var(--color-text-muted);margin-top:4px">SDL applies if annual payroll ≥ R500,000</span>
                </div>
                <div class="form-group">
                  <label class="form-label">Excluded Amounts</label>
                  <input v-model.number="sdl.excluded_amounts" type="number" min="0" step="0.01" class="form-input" />
                </div>
              </div>
            </div>

            <!-- Leave -->
            <div class="section-block">
              <div class="section-block-title" style="margin-bottom:12px">Leave Income</div>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Leave Days Taken</label>
                  <input v-model.number="leave.leave_days_taken" type="number" min="0" max="31" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Total Leave Days Available</label>
                  <input v-model.number="leave.total_leave_days_available" type="number" min="0" max="365" class="form-input" />
                </div>
              </div>
            </div>

            <!-- Calculate & Preview -->
            <div class="section-block">
              <div class="flex items-center gap-2" style="margin-bottom:12px">
                <button @click="previewSalary" class="btn-secondary" :disabled="calculating">
                  {{ calculating ? 'Calculating…' : 'Calculate Preview' }}
                </button>
                <span style="font-size:12.5px;color:var(--color-text-muted)">
                  Earnings: <strong style="color:var(--color-text-base)">R{{ (Number(form.basic_salary||0)+Number(form.other_allowances||0)).toLocaleString('en-ZA') }}</strong>
                  &nbsp;·&nbsp;
                  Deductions: <strong style="color:var(--color-text-base)">R{{ totalDeductions.toLocaleString('en-ZA') }}</strong>
                </span>
              </div>
              <div v-if="previewResult" class="preview-result fade-in">
                <div class="preview-grid">
                  <div class="preview-cell">
                    <div class="preview-label">PAYE</div>
                    <div class="preview-value">R{{ Number(previewResult.paye).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                  <div class="preview-cell">
                    <div class="preview-label">UIF</div>
                    <div class="preview-value">R{{ Number(previewResult.uif).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                  <div class="preview-cell">
                    <div class="preview-label">SDL</div>
                    <div class="preview-value">R{{ Number(previewResult.sdl||0).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                  <div class="preview-cell">
                    <div class="preview-label">Total Earnings</div>
                    <div class="preview-value">R{{ Number(previewResult.total_earnings).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                  <div class="preview-cell">
                    <div class="preview-label">Total Deductions</div>
                    <div class="preview-value">R{{ Number(previewResult.total_deductions).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                  <div class="preview-cell">
                    <div class="preview-label">Net Pay</div>
                    <div class="preview-value net-pay">R{{ Number(previewResult.net_pay).toLocaleString('en-ZA', {minimumFractionDigits:2}) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── Tax Info tab ── -->
          <div v-if="activeTab === 'tax'" class="tab-content fade-in">
            <div class="info-box info-blue" style="margin-bottom:16px">
              SARS tax reference is used on IRP5 certificates and EMP201 returns.
            </div>
            <div class="form-grid">
              <div class="form-group span-2">
                <label class="form-label">Tax Reference Number (SARS)</label>
                <input v-model="form.tax_ref" type="text" class="form-input" placeholder="e.g. 1234567890" />
              </div>
            </div>
          </div>

          <!-- ── Login Credentials tab (create only) ── -->
          <div v-if="activeTab === 'credentials'" class="tab-content fade-in">
            <div class="info-box info-blue" style="margin-bottom:16px">
              Optionally create a portal login for this employee. The account is activated immediately — provide the credentials directly to the employee. Leave blank to skip.
            </div>
            <div class="form-grid">
              <div class="form-group span-2">
                <label class="form-label">Login Email</label>
                <input v-model="creds.login_email" type="email" class="form-input" placeholder="employee@example.com" autocomplete="off" />
              </div>
              <div class="form-group">
                <label class="form-label">Temporary Password</label>
                <div class="pw-field-wrap">
                  <input
                    v-model="creds.login_password"
                    :type="creds.showPassword ? 'text' : 'password'"
                    class="form-input"
                    placeholder="Min 8 characters"
                    autocomplete="new-password"
                  />
                  <button type="button" class="pw-toggle" @click="creds.showPassword = !creds.showPassword">
                    {{ creds.showPassword ? 'Hide' : 'Show' }}
                  </button>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Confirm Password</label>
                <input
                  v-model="creds.login_password_confirm"
                  :type="creds.showPassword ? 'text' : 'password'"
                  class="form-input"
                  placeholder="Repeat password"
                  autocomplete="new-password"
                />
              </div>
            </div>
          </div>

        </div>

        <!-- Drawer footer -->
        <div class="drawer-footer">
          <button @click="close" class="btn-secondary">Cancel</button>
          <button @click="save" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving…' : (editing ? 'Save Changes' : 'Create Employee') }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- ───── CSV Import Modal ───── -->
    <div v-if="showImportModal" class="modal-overlay" style="z-index:500">
      <div class="modal" style="max-width:680px;display:flex;flex-direction:column;max-height:90vh">
        <div class="modal-header" style="flex-shrink:0">
          <h2>Import Employees from CSV</h2>
          <button @click="closeImport" class="modal-close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body" style="flex-shrink:0;border-bottom:1px solid var(--color-border)">
          <p style="font-size:13px;color:var(--color-text-muted);margin-bottom:10px">Upload a CSV file. Download the template first to see the expected column format.</p>
          <input ref="csvFileInput" type="file" accept=".csv" @change="onCsvFile" class="form-input" />
          <p v-if="importError" style="font-size:12px;color:var(--color-error);margin-top:6px">{{ importError }}</p>
        </div>
        <div v-if="importPreview.length" style="flex:1;overflow:auto;padding:16px">
          <p style="font-size:13px;font-weight:500;margin-bottom:8px">Preview — {{ importPreview.length }} row(s)</p>
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th>First Names</th><th>Last Name</th><th>Employee #</th>
                <th>Position</th><th>Basic Salary</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in importPreview" :key="i" :style="row._error ? 'background:#fef2f2' : ''">
                <td>{{ row.first_names }}</td>
                <td>{{ row.last_name }}</td>
                <td>{{ row.employee_no || '—' }}</td>
                <td>{{ row.position || '—' }}</td>
                <td>{{ row.basic_salary }}</td>
                <td>
                  <span v-if="row._error" style="color:var(--color-error);font-size:11px" :title="row._error">⚠ Error</span>
                  <span v-else style="color:var(--color-success);font-size:11px">✓ OK</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="importResult" style="padding:12px 16px;border-top:1px solid var(--color-border);flex-shrink:0">
          <p style="font-size:13px;font-weight:500" :style="importResult.failed > 0 ? 'color:#92400e' : 'color:#166534'">
            Imported {{ importResult.created }} employee(s){{ importResult.failed > 0 ? `, ${importResult.failed} failed` : '' }}.
          </p>
        </div>
        <div class="modal-footer" style="flex-shrink:0;border-radius:0 0 12px 12px">
          <button @click="closeImport" class="btn-secondary">Close</button>
          <button
            @click="confirmImport"
            :disabled="!importPreview.filter(r => !r._error).length || importLoading"
            class="btn-primary"
          >{{ importLoading ? 'Importing…' : `Import ${importPreview.filter(r => !r._error).length} Employees` }}</button>
        </div>
      </div>
    </div>

    <!-- ───── Leave Balance Modal ───── -->
    <div v-if="showLeaveModal" class="modal-overlay" style="z-index:500">
      <div class="modal" style="max-width:560px">
        <div class="modal-header">
          <h2>Leave Balances — {{ leaveEmployee?.first_names }} {{ leaveEmployee?.last_name }}</h2>
          <button @click="showLeaveModal = false" class="modal-close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="flex items-center gap-3" style="flex-wrap:wrap;margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid var(--color-border)">
            <div>
              <label class="form-label">Year</label>
              <input v-model.number="leaveYear" type="number" min="2020" max="2099" class="form-input" style="width:90px" @change="loadLeaveBalances" />
            </div>
            <div>
              <label class="form-label">Leave Type</label>
              <select v-model="newLeave.leave_type" class="form-input">
                <option value="Annual">Annual (21 days)</option>
                <option value="Sick">Sick (30 days / 3yr)</option>
                <option value="Family Responsibility">Family Responsibility (3 days)</option>
                <option value="Unpaid">Unpaid</option>
              </select>
            </div>
            <div>
              <label class="form-label">Allocated</label>
              <input v-model.number="newLeave.days_allocated" type="number" min="0" step="0.5" class="form-input" style="width:70px" />
            </div>
            <div>
              <label class="form-label">Taken</label>
              <input v-model.number="newLeave.days_taken" type="number" min="0" step="0.5" class="form-input" style="width:70px" />
            </div>
            <button @click="addLeaveBalance" class="btn-primary" style="align-self:flex-end">Add</button>
          </div>
          <table v-if="leaveBalances.length" class="data-table">
            <thead>
              <tr>
                <th>Type</th><th style="text-align:right">Allocated</th>
                <th style="text-align:right">Taken</th><th style="text-align:right">Remaining</th><th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in leaveBalances" :key="b.id">
                <td>{{ b.leave_type }}</td>
                <td style="text-align:right"><input v-model.number="b.days_allocated" type="number" min="0" step="0.5" class="form-input" style="width:70px;text-align:right" /></td>
                <td style="text-align:right"><input v-model.number="b.days_taken" type="number" min="0" step="0.5" class="form-input" style="width:70px;text-align:right" /></td>
                <td style="text-align:right;font-weight:600" :style="(b.days_allocated-b.days_taken)<0 ? 'color:var(--color-error)' : 'color:#166534'">
                  {{ Math.max(b.days_allocated-b.days_taken,0).toFixed(1) }}
                </td>
                <td>
                  <div class="actions" style="justify-content:flex-end">
                    <button @click="saveLeaveBalance(b)" class="btn-secondary" style="font-size:12px;height:28px;padding:0 10px">Save</button>
                    <button @click="deleteLeaveBalance(b.id)" class="btn-text danger">✕</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-state" style="padding:24px">No leave balances for {{ leaveYear }}. Add one above.</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { useRoute } from 'vue-router'

const ALL_TABS = [
  { id: 'personal',     label: 'Personal Info' },
  { id: 'banking',      label: 'Banking' },
  { id: 'salary',       label: 'Salary & Deductions' },
  { id: 'tax',          label: 'Tax Info' },
  { id: 'credentials',  label: 'Login Credentials', createOnly: true },
]

export default {
  name: 'EmployeesView',
  setup() {
    const route      = useRoute()
    const auth       = useAuthStore()
    const toast      = useToastStore()
    const companyId  = parseInt(route.params.companyId, 10)

    const employees   = ref([])
    const companyName = ref('')
    const companyObj  = ref(null)
    const showDrawer  = ref(false)
    const editing     = ref(null)
    const activeTab   = ref('personal')
    const saving      = ref(false)
    const calculating = ref(false)
    const viewMode    = ref('active')

    const activeEmployees   = computed(() => employees.value.filter(e => e.is_active))
    const archivedEmployees = computed(() => employees.value.filter(e => !e.is_active))
    const visibleEmployees  = computed(() =>
      viewMode.value === 'archived' ? archivedEmployees.value : activeEmployees.value
    )

    const setView = (mode) => { viewMode.value = mode }

    const TABS = computed(() => ALL_TABS.filter(t => !t.createOnly || !editing.value))

    const form = reactive({
      first_names: '', last_name: '', employee_no: '', id_no: '', position: '',
      tax_ref: '', emp_date: '', is_active: true,
      basic_salary: 0, housing_allowance: 0, transport_allowance: 0,
      meal_allowance: 0, other_allowances: 0,
      pension_contribution: 0, medical_aid: 0, union_fees: 0, other_deductions: 0,
      bank_name: '', account_number: '', branch_code: '', account_type: ''
    })

    const creds = reactive({ login_email: '', login_password: '', login_password_confirm: '', showPassword: false })

    const calcMode     = ref('normal')
    const reverseToggle = ref(false)
    const targetNetPay  = ref(0)
    const sdl  = reactive({ annual_payroll: 0, excluded_amounts: 0 })
    const leave = reactive({ leave_days_taken: 0, total_leave_days_available: 21 })

    const authHeader = () => ({ headers: { Authorization: `Bearer ${auth.accessToken}` } })

    const load = async () => {
      const [emps, company] = await Promise.all([
        axios.get(`/companies/${companyId}/employees`, { ...authHeader(), params: { include_inactive: true } }),
        axios.get(`/companies/${companyId}`, authHeader())
      ])
      employees.value   = emps.data
      companyObj.value  = company.data
      companyName.value = company.data.name
    }

    const resetForm = () => {
      Object.assign(form, {
        first_names:'', last_name:'', employee_no:'', id_no:'', position:'',
        tax_ref:'', emp_date:'', is_active: true,
        basic_salary:0, housing_allowance:0, transport_allowance:0,
        meal_allowance:0, other_allowances:0,
        pension_contribution:0, medical_aid:0, union_fees:0, other_deductions:0,
        bank_name:'', account_number:'', branch_code:'', account_type:''
      })
      Object.assign(creds, { login_email: '', login_password: '', login_password_confirm: '', showPassword: false })
      calcMode.value = 'normal'
      reverseToggle.value = false
      targetNetPay.value = 0
      Object.assign(sdl, { annual_payroll: 0, excluded_amounts: 0 })
      Object.assign(leave, { leave_days_taken: 0, total_leave_days_available: 21 })
      previewResult.value = null
    }

    const openCreate = () => {
      editing.value = null
      resetForm()
      activeTab.value = 'personal'
      showDrawer.value = true
    }

    const openEdit = (emp) => {
      editing.value = emp
      Object.assign(form, emp)
      activeTab.value = 'personal'
      previewResult.value = null
      showDrawer.value = true
    }

    const close = () => { showDrawer.value = false }

    const totalDeductions = computed(() =>
      Number(form.pension_contribution||0) + Number(form.medical_aid||0) +
      Number(form.union_fees||0) + Number(form.other_deductions||0)
    )

    const previewResult = ref(null)

    const previewSalary = async () => {
      calculating.value = true
      try {
        const today = new Date()
        const start = new Date(today.getFullYear(), today.getMonth(), 1)
        const end   = new Date(today.getFullYear(), today.getMonth()+1, 0)
        const common = {
          employee: {
            first_names: form.first_names || '',
            last_name:   form.last_name || '',
            id_no:       form.id_no || '',
            employee_no: form.employee_no || '',
            position:    form.position || '',
            tax_ref:     form.tax_ref || '',
            emp_date:    form.emp_date || start.toISOString().slice(0,10)
          },
          company: {
            company_name:    companyObj.value?.name || '',
            company_reg_no:  companyObj.value?.registration_number || '',
            company_address: companyObj.value?.address || '',
            uif_ref:         companyObj.value?.uif_reference || '',
            phone:           companyObj.value?.phone || '',
            email:           companyObj.value?.email || '',
            run: `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}`
          },
          period_start:    start.toISOString().slice(0,10),
          period_end:      end.toISOString().slice(0,10),
          payment_date:    end.toISOString().slice(0,10),
          annual_payroll:  Number(sdl.annual_payroll || 0),
          excluded_amounts: Number(sdl.excluded_amounts || 0),
          leave_days_taken: Number(leave.leave_days_taken || 0),
          total_leave_days_available: Number(leave.total_leave_days_available || 21),
          company_id: null, employee_id: null
        }

        let data
        if (calcMode.value === 'reverse') {
          const payload = { ...common, target_net_pay: Number(targetNetPay.value||0), other_earnings: Number(form.other_allowances||0), pension: Number(form.pension_contribution||0), medical: Number(form.medical_aid||0) }
          ;({ data } = await axios.post('/calculate-reverse-payroll', payload, authHeader()))
        } else {
          const payload = { ...common, basic_pay: Number(form.basic_salary||0), other_earnings: Number(form.other_allowances||0), pension: Number(form.pension_contribution||0), medical: Number(form.medical_aid||0) }
          ;({ data } = await axios.post('/calculate-payroll', payload, authHeader()))
        }
        previewResult.value = data
      } catch (err) {
        toast.error(`Failed to preview salary: ${err.response?.data?.detail || err.message}`)
      } finally {
        calculating.value = false
      }
    }

    const save = async () => {
      if (!form.first_names || !form.last_name) {
        toast.error('First name and last name are required')
        activeTab.value = 'personal'
        return
      }
      // Validate credentials if provided (create-only)
      if (!editing.value && creds.login_email) {
        if (!creds.login_password) {
          toast.error('Password is required when an email is provided')
          activeTab.value = 'credentials'
          return
        }
        if (creds.login_password.length < 8) {
          toast.error('Password must be at least 8 characters')
          activeTab.value = 'credentials'
          return
        }
        if (creds.login_password !== creds.login_password_confirm) {
          toast.error('Passwords do not match')
          activeTab.value = 'credentials'
          return
        }
      }
      saving.value = true
      try {
        await previewSalary()
        if (editing.value) {
          await axios.put(`/employees/${editing.value.id}`, form, authHeader())
        } else {
          const payload = { ...form }
          if (creds.login_email && creds.login_password) {
            payload.login_email = creds.login_email
            payload.login_password = creds.login_password
          }
          await axios.post(`/companies/${companyId}/employees`, payload, authHeader())
        }
        const successMsg = (!editing.value && creds.login_email)
          ? `Employee created and credentials sent to ${creds.login_email}`
          : (editing.value ? 'Employee updated successfully' : 'Employee created successfully')
        toast.success(successMsg)
        showDrawer.value = false
        await load()
      } catch (err) {
        toast.error(`Failed to save employee: ${err.response?.data?.detail || err.message}`)
      } finally {
        saving.value = false
      }
    }

    // Archive / restore
    const archiveTarget = ref(null)
    const archiving = ref(false)

    const confirmArchive = (emp) => { archiveTarget.value = emp }

    const doArchive = async () => {
      if (!archiveTarget.value) return
      archiving.value = true
      try {
        await axios.delete(`/employees/${archiveTarget.value.id}`, authHeader())
        toast.success(`${archiveTarget.value.first_names} ${archiveTarget.value.last_name} archived.`)
        archiveTarget.value = null
        await load()
      } catch (err) {
        toast.error(`Failed to archive: ${err.response?.data?.detail || err.message}`)
      } finally {
        archiving.value = false
      }
    }

    const restore = async (emp) => {
      try {
        await axios.post(`/employees/${emp.id}/restore`, {}, authHeader())
        toast.success(`${emp.first_names} ${emp.last_name} restored.`)
        await load()
      } catch (err) {
        toast.error(`Failed to restore: ${err.response?.data?.detail || err.message}`)
      }
    }

    // ─── CSV Import ────────────────────────────────────────────────────────────
    const showImportModal = ref(false)
    const csvFileInput    = ref(null)
    const importPreview   = ref([])
    const importError     = ref('')
    const importResult    = ref(null)
    const importLoading   = ref(false)

    const CSV_COLS = ['first_names','last_name','id_no','employee_no','position','tax_ref','emp_date',
      'basic_salary','housing_allowance','transport_allowance','meal_allowance','other_allowances',
      'pension_contribution','medical_aid','union_fees','other_deductions','bank_name','account_number','branch_code','account_type']

    const downloadTemplate = () => {
      const header  = CSV_COLS.join(',')
      const example = 'Jane,Doe,9001010001088,EMP001,Developer,,2023-01-01,25000,0,500,0,0,1000,500,0,0,Standard Bank,123456789,051001,savings'
      const blob = new Blob([header + '\n' + example], { type: 'text/csv' })
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
      a.download = 'employee_import_template.csv'; a.click()
    }

    const parseCsvRow = (line) => {
      const result = []; let cur = ''; let inQ = false
      for (const ch of line) {
        if (ch === '"') { inQ = !inQ }
        else if (ch === ',' && !inQ) { result.push(cur.trim()); cur = '' }
        else { cur += ch }
      }
      result.push(cur.trim())
      return result
    }

    const onCsvFile = (e) => {
      importPreview.value = []; importError.value = ''; importResult.value = null
      const file = e.target.files?.[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = (ev) => {
        const lines = ev.target.result.split('\n').map(l => l.replace(/\r/g, '')).filter(Boolean)
        if (lines.length < 2) { importError.value = 'CSV must have a header row and at least one data row.'; return }
        const headers = parseCsvRow(lines[0]).map(h => h.trim().toLowerCase().replace(/\s+/g,'_'))
        const preview = []
        for (let i = 1; i < lines.length; i++) {
          const vals = parseCsvRow(lines[i])
          const row = {}
          headers.forEach((h, idx) => { row[h] = vals[idx] || '' })
          if (!row.first_names || !row.last_name) row._error = 'first_names and last_name are required'
          const numFields = ['basic_salary','housing_allowance','transport_allowance','meal_allowance','other_allowances','pension_contribution','medical_aid','union_fees','other_deductions']
          numFields.forEach(f => { row[f] = parseFloat(row[f] || '0') || 0 })
          preview.push(row)
        }
        importPreview.value = preview
      }
      reader.readAsText(file)
    }

    const confirmImport = async () => {
      const valid = importPreview.value.filter(r => !r._error)
      if (!valid.length) return
      importLoading.value = true; importResult.value = null
      try {
        const body = valid.map(r => { const emp = {}; CSV_COLS.forEach(c => { if (r[c] !== undefined) emp[c] = r[c] }); return emp })
        const { data } = await axios.post(`/companies/${companyId}/employees/import`, body, authHeader())
        importResult.value = data
        if (data.created > 0) await load()
      } catch (e) {
        importError.value = e?.response?.data?.detail || e?.message || 'Import failed'
      } finally { importLoading.value = false }
    }

    const closeImport = () => {
      showImportModal.value = false; importPreview.value = []; importError.value = ''; importResult.value = null
      if (csvFileInput.value) csvFileInput.value.value = ''
    }

    // ─── Leave Balances ───────────────────────────────────────────────────────
    const showLeaveModal  = ref(false)
    const leaveEmployee   = ref(null)
    const leaveBalances   = ref([])
    const leaveYear       = ref(new Date().getFullYear())
    const newLeave        = reactive({ leave_type: 'Annual', days_allocated: 21, days_taken: 0 })

    const loadLeaveBalances = async () => {
      if (!leaveEmployee.value) return
      try {
        const { data } = await axios.get(`/employees/${leaveEmployee.value.id}/leave-balances?year=${leaveYear.value}`, authHeader())
        leaveBalances.value = data
      } catch {}
    }

    const openLeave = async (emp) => {
      leaveEmployee.value = emp; showLeaveModal.value = true; await loadLeaveBalances()
    }

    const addLeaveBalance = async () => {
      try {
        await axios.post(`/employees/${leaveEmployee.value.id}/leave-balances`, {
          leave_type: newLeave.leave_type, year: leaveYear.value,
          days_allocated: newLeave.days_allocated, days_taken: newLeave.days_taken
        }, authHeader())
        newLeave.days_allocated = 21; newLeave.days_taken = 0
        await loadLeaveBalances()
      } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to add leave balance') }
    }

    const saveLeaveBalance = async (b) => {
      try {
        await axios.put(`/employees/${leaveEmployee.value.id}/leave-balances/${b.id}`,
          { days_allocated: b.days_allocated, days_taken: b.days_taken }, authHeader())
        await loadLeaveBalances()
      } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to update leave balance') }
    }

    const deleteLeaveBalance = async (id) => {
      if (!confirm('Remove this leave balance?')) return
      try {
        await axios.delete(`/employees/${leaveEmployee.value.id}/leave-balances/${id}`, authHeader())
        await loadLeaveBalances()
      } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to delete leave balance') }
    }

    onMounted(load)

    return {
      TABS, companyId, employees, companyName,
      showDrawer, editing, form, creds, activeTab, saving, calculating,
      viewMode, activeEmployees, archivedEmployees, visibleEmployees, setView,
      openCreate, openEdit, close, save,
      archiveTarget, archiving, confirmArchive, doArchive, restore,
      previewSalary, previewResult, totalDeductions,
      calcMode, reverseToggle, targetNetPay, sdl, leave,
      showImportModal, csvFileInput, importPreview, importError, importResult, importLoading,
      downloadTemplate, onCsvFile, confirmImport, closeImport,
      showLeaveModal, leaveEmployee, leaveBalances, leaveYear, newLeave,
      openLeave, loadLeaveBalances, addLeaveBalance, saveLeaveBalance, deleteLeaveBalance
    }
  }
}
</script>

<style scoped>
/* ── View toggle ─────────────────────────────────────────────────────────── */
.view-toggle {
  display: flex;
  gap: 0;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 3px;
  width: fit-content;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border: none;
  background: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
  font-family: inherit;
}

.toggle-btn.active {
  background: var(--color-accent);
  color: #fff;
}

.toggle-btn:not(.active):hover {
  background: var(--color-bg-page);
  color: var(--color-text-base);
}

.count-chip {
  background: rgba(0,0,0,0.12);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  min-width: 20px;
  text-align: center;
}

.toggle-btn.active .count-chip {
  background: rgba(255,255,255,0.25);
}

/* ── Archived row ────────────────────────────────────────────────────────── */
.row-archived td {
  opacity: 0.6;
}

.badge-archived {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  background: #f1f5f9;
  color: #64748b;
}

/* ── Archive modal ───────────────────────────────────────────────────────── */
.archive-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0 0 12px;
}

.archive-detail {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0 0 8px;
}

.archive-list {
  padding-left: 18px;
  margin: 0 0 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.archive-list li {
  font-size: 13px;
  color: var(--color-text-base);
}

.archive-restore-note {
  font-size: 12px;
  color: #15803d;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 6px;
  padding: 8px 12px;
  margin: 0;
}

.btn-danger {
  padding: 8px 18px;
  background: #dc2626;
  color: #fff;
  border: none;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.12s;
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Drawer backdrop ─────────────────────────────────────────────────────── */
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 200;
  backdrop-filter: blur(2px);
}

/* ── Drawer panel ────────────────────────────────────────────────────────── */
.drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 540px;
  max-width: 100vw;
  background: var(--color-bg-card);
  z-index: 201;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.18);
}

/* ── Drawer header ───────────────────────────────────────────────────────── */
.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.drawer-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
}
.drawer-subtitle {
  font-size: 12.5px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* ── Drawer tabs ─────────────────────────────────────────────────────────── */
.drawer-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  overflow-x: auto;
}
.drawer-tab {
  padding: 11px 16px;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  color: var(--color-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
}
.drawer-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.drawer-tab:hover:not(.active) { color: var(--color-text-base); }

/* ── Drawer body ─────────────────────────────────────────────────────────── */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* ── Drawer footer ───────────────────────────────────────────────────────── */
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
  background: #fafbfd;
  flex-shrink: 0;
}

/* ── Section blocks inside drawer ────────────────────────────────────────── */
.section-block {
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 14px;
}
.section-block:last-child { margin-bottom: 0; }
.section-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-block-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
}

/* ── Calc mode toggle ────────────────────────────────────────────────────── */
.calc-mode-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-muted);
}
.mode-active { font-weight: 600; color: var(--color-text-base); }

/* ── Toggle switch ───────────────────────────────────────────────────────── */
.toggle-switch { position: relative; display: inline-block; cursor: pointer; }
.toggle-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.toggle-track {
  display: block;
  width: 38px;
  height: 21px;
  background: var(--color-border-input);
  border-radius: 999px;
  transition: background 0.2s;
  position: relative;
}
.toggle-switch input:checked + .toggle-track { background: var(--color-accent); }
.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 15px;
  height: 15px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s;
}
.toggle-switch input:checked + .toggle-track .toggle-thumb { transform: translateX(17px); }

/* ── Preview result ──────────────────────────────────────────────────────── */
.preview-result {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 14px;
}
.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.preview-label { font-size: 11.5px; color: var(--color-text-muted); margin-bottom: 3px; }
.preview-value { font-size: 14px; font-weight: 600; color: var(--color-text-base); }
.preview-value.net-pay { color: #166534; }

/* ── Tab content ─────────────────────────────────────────────────────────── */
.tab-content { min-height: 0; }

/* ── Password field with show/hide ──────────────────────────────────────── */
.pw-field-wrap { position: relative; display: flex; }
.pw-field-wrap .form-input { padding-right: 52px; flex: 1; }
.pw-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-accent);
  cursor: pointer;
  padding: 0;
  font-family: inherit;
}
.pw-toggle:hover { text-decoration: underline; }

/* ── Required asterisk ───────────────────────────────────────────────────── */
.req { color: var(--color-error); margin-left: 2px; }

/* ── Transitions ─────────────────────────────────────────────────────────── */
.drawer-backdrop-enter-active, .drawer-backdrop-leave-active { transition: opacity 0.22s; }
.drawer-backdrop-enter-from, .drawer-backdrop-leave-to { opacity: 0; }

.drawer-slide-enter-active { transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.drawer-slide-leave-active { transition: transform 0.2s cubic-bezier(0.4, 0, 1, 1); }
.drawer-slide-enter-from, .drawer-slide-leave-to { transform: translateX(100%); }

/* ── Mobile ──────────────────────────────────────────────────────────────── */
@media (max-width: 600px) {
  .drawer { width: 100vw; }
  .preview-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>

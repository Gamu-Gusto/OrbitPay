<template>
  <div class="portal-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">My Portal</h1>
        <div class="breadcrumb">
          <span>Employee</span>
          <span class="sep">/</span>
          <span>{{ tabLabel }}</span>
        </div>
      </div>
    </div>

    <SkeletonEmployeePortal v-if="loading" />

    <div v-else-if="noProfile" class="card warn-card">
      <svg class="warn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <div>
        <p class="warn-title">No employee profile linked</p>
        <p class="warn-sub">Your account has not been linked to an employee record. Please contact your administrator.</p>
      </div>
    </div>

    <template v-else>

      <!-- Tab bar -->
      <div class="tab-bar">
        <button v-for="t in tabs" :key="t.id" @click="setTab(t.id)"
                class="tab-btn" :class="{ 'is-active': activeTab === t.id }">
          {{ t.label }}
          <span v-if="t.badge > 0" class="tab-badge">{{ t.badge }}</span>
        </button>
      </div>

      <!-- ── DASHBOARD ─────────────────────────────────────────────────── -->
      <template v-if="activeTab === 'dashboard'">

        <!-- Welcome card -->
        <div class="card welcome-card">
          <div class="welcome-avatar">{{ avatarInitials }}</div>
          <div class="welcome-info">
            <p class="welcome-name">{{ dash.employee.first_names }} {{ dash.employee.last_name }}</p>
            <p class="welcome-position">{{ dash.employee.position || '—' }} <span v-if="dash.employee.department">· {{ dash.employee.department }}</span></p>
            <div class="profile-meta">
              <span class="meta-item"><span class="meta-label">Employee #</span><span class="meta-value">{{ dash.employee.employee_no || '—' }}</span></span>
              <span class="meta-sep">·</span>
              <span class="meta-item"><span class="meta-label">Since</span><span class="meta-value">{{ fmtDate(dash.employee.emp_date) }}</span></span>
              <template v-if="dash.employee.employment_type">
                <span class="meta-sep">·</span>
                <span class="meta-item"><span class="meta-value">{{ dash.employee.employment_type }}</span></span>
              </template>
            </div>
          </div>
        </div>

        <!-- Cards grid -->
        <div class="cards-grid">

          <!-- Leave balances -->
          <div class="card dash-card">
            <p class="dash-card-title">Leave Balances</p>
            <div v-if="!dash.leave_balances.length" class="dash-empty">No leave balances on record.</div>
            <div v-else class="leave-list">
              <div v-for="b in dash.leave_balances" :key="b.leave_type" class="leave-item">
                <div class="leave-item-header">
                  <span class="leave-type">{{ b.leave_type }}</span>
                  <span class="leave-stat">{{ b.days_remaining }} / {{ b.days_allocated }} days</span>
                </div>
                <div class="leave-bar-track">
                  <div class="leave-bar-fill" :style="{ width: Math.min(100, (b.days_remaining / b.days_allocated) * 100) + '%' }"></div>
                </div>
              </div>
            </div>
            <button class="dash-link" @click="setTab('payslips')">View all payslips →</button>
          </div>

          <!-- Recent payslips -->
          <div class="card dash-card">
            <p class="dash-card-title">Recent Payslips</p>
            <div v-if="!dash.recent_payslips.length" class="dash-empty">No payslips shared yet.</div>
            <div v-else class="recent-slips">
              <div v-for="slip in dash.recent_payslips" :key="slip.id" class="recent-slip-row">
                <span class="recent-slip-period">{{ slip.period || '—' }}</span>
                <span class="recent-slip-net">{{ fmtMoney(slip.net_pay) }}</span>
                <button @click="downloadPayslip(slip.id)" :disabled="downloading === slip.id" class="btn-light btn-sm">
                  {{ downloading === slip.id ? '…' : 'PDF' }}
                </button>
              </div>
            </div>
            <button class="dash-link" @click="setTab('payslips')">View all →</button>
          </div>

          <!-- Pending requests -->
          <div class="card dash-card">
            <p class="dash-card-title">Pending Requests</p>
            <div class="pending-list">
              <div class="pending-item" @click="setTab('requests')" style="cursor:pointer">
                <span class="pending-label">Leave requests</span>
                <span class="pending-count" :class="dash.pending_counts.leave > 0 ? 'count-yellow' : 'count-zero'">{{ dash.pending_counts.leave }}</span>
              </div>
              <div class="pending-item" @click="setTab('documents')" style="cursor:pointer">
                <span class="pending-label">Documents</span>
                <span class="pending-count" :class="dash.pending_counts.documents > 0 ? 'count-yellow' : 'count-zero'">{{ dash.pending_counts.documents }}</span>
              </div>
              <div class="pending-item" @click="setTab('requests')" style="cursor:pointer">
                <span class="pending-label">Banking changes</span>
                <span class="pending-count" :class="dash.pending_counts.banking > 0 ? 'count-yellow' : 'count-zero'">{{ dash.pending_counts.banking }}</span>
              </div>
            </div>
          </div>

          <!-- Upcoming public holidays -->
          <div class="card dash-card">
            <p class="dash-card-title">Upcoming Public Holidays</p>
            <div v-if="!dash.upcoming_holidays.length" class="dash-empty">No upcoming holidays found.</div>
            <div v-else class="holiday-list">
              <div v-for="h in dash.upcoming_holidays" :key="h.date" class="holiday-item">
                <div class="holiday-days-away">{{ h.days_away === 0 ? 'Today' : h.days_away === 1 ? 'Tomorrow' : h.days_away + 'd' }}</div>
                <div class="holiday-info">
                  <p class="holiday-name">{{ h.name }}</p>
                  <p class="holiday-date">{{ fmtDate(h.date) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Company announcements -->
          <div class="card dash-card">
            <p class="dash-card-title">Announcements <span v-if="unreadAnnouncementCount > 0" class="dash-unread-dot">{{ unreadAnnouncementCount }} new</span></p>
            <div v-if="!dash.announcements.length" class="dash-empty">No announcements.</div>
            <div v-else class="ann-list">
              <div v-for="a in dash.announcements" :key="a.id" class="ann-item">
                <p class="ann-title">{{ a.title }}</p>
                <p class="ann-preview">{{ a.body.length > 80 ? a.body.slice(0, 80) + '…' : a.body }}</p>
              </div>
            </div>
            <button class="dash-link" @click="setTab('announcements')">Read more →</button>
          </div>

          <!-- My tasks -->
          <div class="card dash-card">
            <p class="dash-card-title">My Tasks</p>
            <div v-if="!dash.pending_tasks.length" class="dash-empty">All tasks complete!</div>
            <div v-else class="task-list">
              <div v-for="task in dash.pending_tasks" :key="task.id" class="task-item">
                <button @click="completeTask(task.id)" class="task-check" :disabled="completingTask === task.id" title="Mark complete">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                </button>
                <div class="task-info">
                  <p class="task-title">{{ task.title }}</p>
                  <p v-if="task.due_date" class="task-due">Due {{ fmtDate(task.due_date) }}</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </template>

      <!-- ── MY PROFILE ─────────────────────────────────────────────────── -->
      <template v-else-if="activeTab === 'profile'">
        <div v-if="profileLoading" class="loading-state"><div class="spinner"></div><span>Loading…</span></div>
        <template v-else>

          <!-- Profile picture -->
          <div class="card profile-pic-card">
            <div class="profile-avatar-lg">
              <img v-if="profileData.profile_picture_data" :src="'data:image/jpeg;base64,' + profileData.profile_picture_data" class="avatar-img" alt="Profile" />
              <span v-else>{{ avatarInitials }}</span>
            </div>
            <div class="profile-pic-actions">
              <p class="profile-pic-label">Profile picture (JPEG/PNG, max 2 MB)</p>
              <input ref="picInput" type="file" accept="image/jpeg,image/png" class="hidden-file-input" @change="onPicChange" />
              <button @click="$refs.picInput.click()" :disabled="picUploading" class="btn-light btn-sm">{{ picUploading ? 'Uploading…' : 'Change photo' }}</button>
              <span v-if="picError" class="form-error">{{ picError }}</span>
            </div>
          </div>

          <!-- Personal & contact info -->
          <section class="section">
            <h2 class="section-title">Personal &amp; Contact Information</h2>
            <div class="card">
              <div class="form-grid-2">
                <div class="form-group">
                  <label class="form-label">First Names</label>
                  <input v-model="profileForm.first_names" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Last Name</label>
                  <input v-model="profileForm.last_name" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Phone</label>
                  <input v-model="profileForm.phone" type="tel" class="form-input" placeholder="+27…" />
                </div>
                <div class="form-group">
                  <label class="form-label">Personal Email</label>
                  <input v-model="profileForm.personal_email" type="email" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Street Address</label>
                  <input v-model="profileForm.address_street" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">City</label>
                  <input v-model="profileForm.address_city" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Province</label>
                  <input v-model="profileForm.address_province" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Postal Code</label>
                  <input v-model="profileForm.address_postal_code" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Tax Number</label>
                  <input v-model="profileForm.tax_number" type="text" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Tax Reference</label>
                  <input v-model="profileForm.tax_ref" type="text" class="form-input" />
                </div>
              </div>
              <div class="form-actions-row" style="margin-top:16px">
                <span v-if="profileSaveError" class="form-error">{{ profileSaveError }}</span>
                <span v-if="profileSaveSuccess" class="form-success">Saved.</span>
                <button @click="saveProfile" :disabled="profileSaving" class="btn-primary btn-sm">
                  {{ profileSaving ? 'Saving…' : 'Save Changes' }}
                </button>
              </div>
            </div>
          </section>

          <!-- Read-only employment details -->
          <section class="section">
            <h2 class="section-title">Employment Details (read-only)</h2>
            <div class="card">
              <div class="readonly-grid">
                <div class="readonly-item"><span class="readonly-label">Position</span><span class="readonly-val">{{ profileData.position || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Department</span><span class="readonly-val">{{ profileData.department || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Employment Type</span><span class="readonly-val">{{ profileData.employment_type || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Reporting Manager</span><span class="readonly-val">{{ profileData.reporting_manager || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Employee #</span><span class="readonly-val">{{ profileData.employee_no || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Start Date</span><span class="readonly-val">{{ fmtDate(profileData.emp_date) }}</span></div>
                <div class="readonly-item"><span class="readonly-label">ID Number</span><span class="readonly-val">{{ profileData.id_no || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Status</span><span class="readonly-val">{{ profileData.is_active ? 'Active' : 'Inactive' }}</span></div>
              </div>
            </div>
          </section>

          <!-- Emergency contacts -->
          <section class="section">
            <h2 class="section-title">Emergency Contacts</h2>
            <div class="card">
              <div v-if="!emergencyContacts.length" class="empty-state">No emergency contacts on record.</div>
              <div v-else class="ec-list">
                <div v-for="ec in emergencyContacts" :key="ec.id" class="ec-row">
                  <div class="ec-info">
                    <span class="ec-name">{{ ec.full_name }}</span>
                    <span class="ec-rel">{{ ec.relationship }}</span>
                    <span class="ec-phone">{{ ec.phone }}</span>
                    <span v-if="ec.is_primary" class="badge badge-blue" style="font-size:10px">Primary</span>
                  </div>
                  <div class="ec-actions">
                    <button @click="editEC(ec)" class="btn-light btn-sm">Edit</button>
                    <button @click="deleteEC(ec.id)" class="btn-light btn-sm" style="color:#dc2626">Delete</button>
                  </div>
                </div>
              </div>

              <!-- Add / edit form -->
              <div class="ec-form-wrap">
                <p class="banking-label" style="margin-bottom:10px">{{ ecForm.id ? 'Edit contact' : 'Add contact' }}</p>
                <div class="form-grid-2">
                  <div class="form-group">
                    <label class="form-label">Full Name *</label>
                    <input v-model="ecForm.full_name" type="text" class="form-input" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Relationship *</label>
                    <input v-model="ecForm.relationship" type="text" class="form-input" placeholder="e.g. Spouse" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Phone *</label>
                    <input v-model="ecForm.phone" type="tel" class="form-input" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Email</label>
                    <input v-model="ecForm.email" type="email" class="form-input" />
                  </div>
                </div>
                <div class="form-group" style="margin-top:8px">
                  <label class="checkbox-label">
                    <input v-model="ecForm.is_primary" type="checkbox" />
                    Primary contact
                  </label>
                </div>
                <div class="form-actions-row" style="margin-top:12px">
                  <span v-if="ecError" class="form-error">{{ ecError }}</span>
                  <button v-if="ecForm.id" @click="cancelECEdit" class="btn-light btn-sm">Cancel</button>
                  <button @click="saveEC" :disabled="ecSaving || !ecForm.full_name || !ecForm.relationship || !ecForm.phone" class="btn-primary btn-sm">
                    {{ ecSaving ? 'Saving…' : ecForm.id ? 'Update' : 'Add Contact' }}
                  </button>
                </div>
              </div>
            </div>
          </section>

          <!-- Banking (read-only + change request link) -->
          <section class="section">
            <h2 class="section-title">Banking Details</h2>
            <div class="card">
              <div class="readonly-grid">
                <div class="readonly-item"><span class="readonly-label">Bank</span><span class="readonly-val">{{ profileData.bank_name || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Account</span><span class="readonly-val">{{ profileData.bank_account_last4 ? '•••• ' + profileData.bank_account_last4 : (profileData.account_number || '—') }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Type</span><span class="readonly-val">{{ profileData.account_type || '—' }}</span></div>
                <div class="readonly-item"><span class="readonly-label">Branch Code</span><span class="readonly-val">{{ profileData.branch_code || '—' }}</span></div>
              </div>
              <div style="margin-top:14px">
                <button @click="setTab('requests')" class="btn-light btn-sm">Request banking change →</button>
              </div>
            </div>
          </section>

        </template>
      </template>

      <!-- ── MY PAYSLIPS ────────────────────────────────────────────────── -->
      <template v-else-if="activeTab === 'payslips'">
        <div v-if="payslipsLoading" class="loading-state"><div class="spinner"></div><span>Loading…</span></div>
        <template v-else>

          <section class="section">
            <h2 class="section-title">My Payslips</h2>
            <div class="card">
              <div v-if="!payslips.length" class="empty-state">No payslips have been shared with you yet.</div>
              <template v-else>
                <div class="table-wrap">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Gross Pay</th>
                        <th>Deductions</th>
                        <th>Net Pay</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="slip in pagedPayslips" :key="slip.id">
                        <td>{{ slip.period || '—' }}</td>
                        <td>{{ fmtMoney(slip.total_earnings) }}</td>
                        <td>{{ fmtMoney(slip.total_deductions) }}</td>
                        <td class="net-pay-cell">{{ fmtMoney(slip.net_pay) }}</td>
                        <td>
                          <button @click="downloadPayslip(slip.id)" :disabled="downloading === slip.id" class="btn-light btn-sm">
                            {{ downloading === slip.id ? 'Downloading…' : 'Download' }}
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div class="pagination" v-if="payslips.length > pageSize">
                  <button @click="prevPage" :disabled="page === 0" class="btn-light page-btn">← Prev</button>
                  <span class="page-info">Page {{ page + 1 }} of {{ totalPages }}</span>
                  <button @click="nextPage" :disabled="page >= totalPages - 1" class="btn-light page-btn">Next →</button>
                </div>
              </template>
            </div>
          </section>

          <!-- Salary history (last 12 payslips as table) -->
          <section v-if="payslips.length > 0" class="section">
            <h2 class="section-title">Salary History (last 12 months)</h2>
            <div class="card">
              <div class="table-wrap">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Basic Pay</th>
                      <th>Total Earnings</th>
                      <th>Total Deductions</th>
                      <th>Net Pay</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="slip in salaryHistory" :key="'h' + slip.id">
                      <td>{{ slip.period || '—' }}</td>
                      <td>{{ fmtMoney(slip.basic_pay) }}</td>
                      <td>{{ fmtMoney(slip.total_earnings) }}</td>
                      <td>{{ fmtMoney(slip.total_deductions) }}</td>
                      <td class="net-pay-cell">{{ fmtMoney(slip.net_pay) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- Tax documents -->
          <section class="section">
            <h2 class="section-title">Tax Documents</h2>
            <div class="card empty-state-card">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <p class="empty-state">Your tax documents (IRP5, IT3a) will appear here when generated.</p>
            </div>
          </section>

        </template>
      </template>

      <!-- ── DOCUMENTS ──────────────────────────────────────────────────── -->
      <template v-else-if="activeTab === 'documents'">
        <div v-if="docsLoading" class="loading-state"><div class="spinner"></div><span>Loading…</span></div>
        <template v-else>

          <section class="section">
            <h2 class="section-title">Upload Document</h2>
            <div class="card">
              <div class="form-grid-3">
                <div class="form-group">
                  <label class="form-label">Document Type *</label>
                  <select v-model="docForm.document_type" class="form-input">
                    <option value="">Select type</option>
                    <option>ID / Passport</option>
                    <option>Proof of Address</option>
                    <option>Bank Statement</option>
                    <option>Tax Certificate</option>
                    <option>Contract</option>
                    <option>Other</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">Description (optional)</label>
                  <input v-model="docForm.description" type="text" class="form-input" placeholder="Brief description…" />
                </div>
                <div class="form-group">
                  <label class="form-label">File (max 5 MB)</label>
                  <input ref="fileInput" type="file" class="form-input file-input" @change="onFileChange" />
                </div>
              </div>
              <div class="form-actions-row">
                <span v-if="docUploadError" class="form-error">{{ docUploadError }}</span>
                <button @click="uploadDocument" :disabled="docUploading || !docForm.document_type || !docForm.file" class="btn-primary btn-sm">
                  {{ docUploading ? 'Uploading…' : 'Upload Document' }}
                </button>
              </div>
              <div v-if="docUploadSuccess" class="success-banner">Document uploaded and pending review.</div>
            </div>
          </section>

          <section class="section">
            <h2 class="section-title">My Documents</h2>
            <div class="card">
              <div v-if="!documents.length" class="empty-state">No documents uploaded yet.</div>
              <div v-else class="doc-list">
                <div v-for="doc in documents" :key="doc.id" class="doc-row">
                  <div class="doc-info">
                    <span class="doc-name">{{ doc.file_name }}</span>
                    <span class="doc-type">{{ doc.document_type }}</span>
                  </div>
                  <div class="doc-meta">
                    <span class="badge" :class="statusBadge(doc.status)">{{ doc.status }}</span>
                    <span v-if="doc.status === 'rejected' && doc.rejection_reason" class="rejection-reason">{{ doc.rejection_reason }}</span>
                    <button @click="downloadDoc(doc.id, doc.file_name)" class="btn-light btn-sm">Download</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="section">
            <h2 class="section-title">Documents Shared by Your Employer</h2>
            <div class="card">
              <div v-if="!policyDocs.length" class="empty-state">No documents have been shared with you yet.</div>
              <div v-else class="doc-list">
                <div v-for="doc in policyDocs" :key="'pd' + doc.id" class="doc-row">
                  <div class="doc-info">
                    <span class="doc-name">{{ doc.title }}</span>
                    <span class="doc-type">{{ doc.file_name }}</span>
                  </div>
                  <div class="doc-meta">
                    <span class="doc-type">{{ fmtDate(doc.uploaded_at) }}</span>
                    <button @click="downloadPolicyDoc(doc.id, doc.file_name)" class="btn-light btn-sm">Download</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

        </template>
      </template>

      <!-- ── REQUESTS ────────────────────────────────────────────────────── -->
      <template v-else-if="activeTab === 'requests'">
        <div v-if="requestsLoading" class="loading-state"><div class="spinner"></div><span>Loading…</span></div>
        <template v-else>

          <!-- Unified timeline -->
          <section class="section">
            <h2 class="section-title">All Requests</h2>
            <div class="card">
              <div v-if="!allRequests.length" class="empty-state">No requests submitted yet.</div>
              <div v-else class="timeline">
                <div v-for="item in allRequests" :key="item._key" class="timeline-item">
                  <div class="tl-icon-wrap">
                    <div class="tl-icon" :class="item._type">
                      <svg v-if="item._type === 'leave'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                      </svg>
                      <svg v-else-if="item._type === 'document'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                      </svg>
                      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>
                      </svg>
                    </div>
                  </div>
                  <div class="tl-body">
                    <div class="tl-header">
                      <span class="tl-label">{{ item._label }}</span>
                      <span class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
                    </div>
                    <p class="tl-detail">{{ item._detail }}</p>
                    <p class="tl-date">{{ fmtDate(item._date) }}</p>
                    <p v-if="item.rejection_reason || item.reason" class="tl-reason">Reason: {{ item.rejection_reason || item.reason }}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Banking change -->
          <section class="section">
            <h2 class="section-title">Banking Details</h2>
            <div class="card">
              <div class="banking-current">
                <p class="banking-label">Current Details</p>
                <div class="banking-fields">
                  <span class="banking-field"><span class="meta-label">Bank</span> <span class="meta-value">{{ dash.employee.bank_name || '—' }}</span></span>
                  <span class="banking-field"><span class="meta-label">Account</span> <span class="meta-value">{{ dash.employee.bank_account_last4 ? '•••• ' + dash.employee.bank_account_last4 : (dash.employee.account_number || '—') }}</span></span>
                  <span class="banking-field"><span class="meta-label">Type</span> <span class="meta-value">{{ dash.employee.account_type || '—' }}</span></span>
                  <span class="banking-field"><span class="meta-label">Branch</span> <span class="meta-value">{{ dash.employee.branch_code || '—' }}</span></span>
                </div>
              </div>

              <div v-if="pendingBankingChange" class="pending-change-banner">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="pending-icon">
                  <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                </svg>
                <div>
                  <p class="pending-title">Change request pending review</p>
                  <p class="pending-sub">{{ pendingBankingChange.new_bank_name }} · {{ pendingBankingChange.new_account_number }} · {{ pendingBankingChange.new_account_type }}</p>
                </div>
              </div>

              <template v-else>
                <div class="banking-divider"></div>
                <p class="banking-label">Request a Change</p>
                <div class="form-grid-2">
                  <div class="form-group">
                    <label class="form-label">New Bank Name</label>
                    <input v-model="bankForm.new_bank_name" type="text" class="form-input" placeholder="e.g. FNB" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">New Account Number</label>
                    <input v-model="bankForm.new_account_number" type="text" class="form-input" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Account Type</label>
                    <select v-model="bankForm.new_account_type" class="form-input">
                      <option value="">Select type</option>
                      <option>Cheque</option>
                      <option>Savings</option>
                      <option>Transmission</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label class="form-label">Branch Code</label>
                    <input v-model="bankForm.new_branch_code" type="text" class="form-input" placeholder="6-digit code" />
                  </div>
                </div>
                <div class="form-actions-row" style="margin-top:12px">
                  <span v-if="bankChangeError" class="form-error">{{ bankChangeError }}</span>
                  <button @click="submitBankingChange" :disabled="bankSubmitting || !bankForm.new_bank_name || !bankForm.new_account_number" class="btn-primary btn-sm">
                    {{ bankSubmitting ? 'Submitting…' : 'Submit Change Request' }}
                  </button>
                </div>
                <div v-if="bankChangeSuccess" class="success-banner">Banking change request submitted for review.</div>
              </template>
            </div>
          </section>

        </template>
      </template>

      <!-- ── ANNOUNCEMENTS ──────────────────────────────────────────────── -->
      <template v-else-if="activeTab === 'announcements'">
        <div v-if="annLoading" class="loading-state"><div class="spinner"></div><span>Loading…</span></div>
        <template v-else>
          <div v-if="!announcements.length" class="card empty-state-card">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 01-3.46 0"/>
            </svg>
            <p class="empty-state">No announcements at this time.</p>
          </div>
          <div v-else class="ann-full-list">
            <div v-for="a in announcements" :key="a.id" class="card ann-full-card">
              <div class="ann-full-header">
                <p class="ann-full-title">{{ a.title }}</p>
                <p class="ann-full-date">{{ fmtDate(a.created_at) }}</p>
              </div>
              <p class="ann-full-body">{{ a.body }}</p>
            </div>
          </div>
        </template>
      </template>

    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import SkeletonEmployeePortal from '../components/ui/SkeletonEmployeePortal.vue'

export default {
  name: 'EmployeePortalView',
  components: { SkeletonEmployeePortal },
  setup() {
    const route = useRoute()
    const router = useRouter()

    const loading = ref(true)
    const noProfile = ref(false)

    // ── Tab management ────────────────────────────────────────────────────
    const activeTab = computed(() => route.query.tab || 'dashboard')
    const setTab = (id) => router.push({ query: { tab: id } })

    // ── Dashboard data (single aggregation call) ──────────────────────────
    const dash = reactive({
      employee: {},
      leave_balances: [],
      recent_payslips: [],
      pending_counts: { leave: 0, documents: 0, banking: 0 },
      upcoming_holidays: [],
      announcements: [],
      pending_tasks: []
    })

    // ── localStorage unread tracking ──────────────────────────────────────
    const _loadReadIds = () => {
      try { return new Set(JSON.parse(localStorage.getItem('orbp_read_ann') || '[]')) }
      catch { return new Set() }
    }
    const readAnnIds = ref(_loadReadIds())
    const _saveReadIds = () => localStorage.setItem('orbp_read_ann', JSON.stringify([...readAnnIds.value]))

    const unreadAnnouncementCount = computed(() =>
      dash.announcements.filter(a => !readAnnIds.value.has(a.id)).length
    )

    const totalPendingCount = computed(() =>
      (dash.pending_counts.leave || 0) + (dash.pending_counts.documents || 0) + (dash.pending_counts.banking || 0)
    )

    const tabs = computed(() => [
      { id: 'dashboard', label: 'Dashboard', badge: 0 },
      { id: 'profile', label: 'My Profile', badge: 0 },
      { id: 'payslips', label: 'My Payslips', badge: 0 },
      { id: 'documents', label: 'Documents', badge: 0 },
      { id: 'requests', label: 'Requests', badge: totalPendingCount.value },
      { id: 'announcements', label: 'Announcements', badge: unreadAnnouncementCount.value }
    ])

    const TAB_LABELS = {
      dashboard: 'Dashboard', profile: 'My Profile', payslips: 'My Payslips',
      documents: 'Documents', requests: 'Requests', announcements: 'Announcements'
    }
    const tabLabel = computed(() => TAB_LABELS[activeTab.value] || 'Dashboard')

    const avatarInitials = computed(() => {
      const f = dash.employee.first_names || ''
      const l = dash.employee.last_name || ''
      return ((f[0] || '') + (l[0] || '')).toUpperCase() || '?'
    })

    // ── Tasks ─────────────────────────────────────────────────────────────
    const completingTask = ref(null)
    const completeTask = async (id) => {
      completingTask.value = id
      try {
        await axios.patch(`/portal/tasks/${id}/complete`)
        const idx = dash.pending_tasks.findIndex(t => t.id === id)
        if (idx !== -1) dash.pending_tasks.splice(idx, 1)
      } catch { /* silent */ } finally {
        completingTask.value = null
      }
    }

    // ── Dashboard load ────────────────────────────────────────────────────
    const loadDashboard = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/portal/dashboard-summary')
        Object.assign(dash, data)
      } catch (e) {
        if (e?.response?.status === 404) noProfile.value = true
        else noProfile.value = true
      } finally {
        loading.value = false
      }
    }

    // ── Profile tab ───────────────────────────────────────────────────────
    const profileLoading = ref(false)
    const profileData = ref({})
    const profileForm = reactive({})
    const profileSaving = ref(false)
    const profileSaveError = ref('')
    const profileSaveSuccess = ref(false)
    const picUploading = ref(false)
    const picError = ref('')
    const emergencyContacts = ref([])
    const ecForm = reactive({ id: null, full_name: '', relationship: '', phone: '', email: '', is_primary: false })
    const ecSaving = ref(false)
    const ecError = ref('')

    const loadProfileTab = async () => {
      if (profileLoading.value) return
      profileLoading.value = true
      try {
        const [profRes, ecRes] = await Promise.allSettled([
          axios.get('/portal/profile'),
          axios.get('/portal/emergency-contacts')
        ])
        if (profRes.status === 'fulfilled') {
          profileData.value = profRes.value.data
          Object.assign(profileForm, {
            first_names: profRes.value.data.first_names,
            last_name: profRes.value.data.last_name,
            phone: profRes.value.data.phone || '',
            personal_email: profRes.value.data.personal_email || '',
            address_street: profRes.value.data.address_street || '',
            address_city: profRes.value.data.address_city || '',
            address_province: profRes.value.data.address_province || '',
            address_postal_code: profRes.value.data.address_postal_code || '',
            tax_number: profRes.value.data.tax_number || '',
            tax_ref: profRes.value.data.tax_ref || ''
          })
        }
        if (ecRes.status === 'fulfilled') emergencyContacts.value = ecRes.value.data || []
      } finally {
        profileLoading.value = false
      }
    }

    const saveProfile = async () => {
      profileSaveError.value = ''
      profileSaveSuccess.value = false
      profileSaving.value = true
      try {
        const { data } = await axios.patch('/portal/profile', profileForm)
        profileData.value = data
        profileSaveSuccess.value = true
        setTimeout(() => { profileSaveSuccess.value = false }, 3000)
      } catch (e) {
        profileSaveError.value = e?.response?.data?.detail || 'Failed to save.'
      } finally {
        profileSaving.value = false
      }
    }

    const onPicChange = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      if (!['image/jpeg', 'image/png'].includes(file.type)) { picError.value = 'Only JPEG or PNG allowed.'; return }
      if (file.size > 2 * 1024 * 1024) { picError.value = 'File must be under 2 MB.'; return }
      picError.value = ''
      picUploading.value = true
      try {
        const fd = new FormData()
        fd.append('file', file)
        const { data } = await axios.post('/portal/profile-picture', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        profileData.value = { ...profileData.value, profile_picture_data: data.profile_picture_data }
      } catch (e) {
        picError.value = e?.response?.data?.detail || 'Upload failed.'
      } finally {
        picUploading.value = false
      }
    }

    const editEC = (ec) => {
      ecForm.id = ec.id
      ecForm.full_name = ec.full_name
      ecForm.relationship = ec.relationship
      ecForm.phone = ec.phone
      ecForm.email = ec.email || ''
      ecForm.is_primary = ec.is_primary
    }

    const cancelECEdit = () => {
      ecForm.id = null; ecForm.full_name = ''; ecForm.relationship = ''; ecForm.phone = ''; ecForm.email = ''; ecForm.is_primary = false
    }

    const saveEC = async () => {
      ecError.value = ''
      ecSaving.value = true
      try {
        const payload = { full_name: ecForm.full_name, relationship: ecForm.relationship, phone: ecForm.phone, email: ecForm.email || undefined, is_primary: ecForm.is_primary }
        if (ecForm.id) {
          const { data } = await axios.patch(`/portal/emergency-contacts/${ecForm.id}`, payload)
          const idx = emergencyContacts.value.findIndex(c => c.id === ecForm.id)
          if (idx !== -1) emergencyContacts.value[idx] = data
        } else {
          const { data } = await axios.post('/portal/emergency-contacts', payload)
          emergencyContacts.value.push(data)
        }
        cancelECEdit()
      } catch (e) {
        ecError.value = e?.response?.data?.detail || 'Failed to save.'
      } finally {
        ecSaving.value = false
      }
    }

    const deleteEC = async (id) => {
      if (!confirm('Delete this emergency contact?')) return
      try {
        await axios.delete(`/portal/emergency-contacts/${id}`)
        emergencyContacts.value = emergencyContacts.value.filter(c => c.id !== id)
      } catch { alert('Failed to delete.') }
    }

    // ── Payslips tab ──────────────────────────────────────────────────────
    const payslipsLoading = ref(false)
    const payslips = ref([])
    const page = ref(0)
    const pageSize = 10
    const totalPages = computed(() => Math.max(1, Math.ceil(payslips.value.length / pageSize)))
    const pagedPayslips = computed(() => payslips.value.slice(page.value * pageSize, (page.value + 1) * pageSize))
    const salaryHistory = computed(() => payslips.value.slice(0, 12))
    const prevPage = () => { if (page.value > 0) page.value-- }
    const nextPage = () => { if (page.value < totalPages.value - 1) page.value++ }

    const loadPayslipsTab = async () => {
      if (payslipsLoading.value) return
      payslipsLoading.value = true
      try {
        const { data } = await axios.get('/portal/payslips')
        payslips.value = data || []
      } finally {
        payslipsLoading.value = false
      }
    }

    const downloading = ref(null)
    const downloadPayslip = async (id) => {
      downloading.value = id
      try {
        const res = await axios.get(`/payroll-records/${id}/payslip`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.setAttribute('download', `payslip_${id}.pdf`)
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch { alert('Failed to download payslip.') } finally {
        downloading.value = null
      }
    }

    // ── Documents tab ─────────────────────────────────────────────────────
    const docsLoading = ref(false)
    const documents = ref([])
    const policyDocs = ref([])
    const fileInput = ref(null)
    const docForm = reactive({ document_type: '', description: '', file: null })
    const docUploading = ref(false)
    const docUploadError = ref('')
    const docUploadSuccess = ref(false)

    const onFileChange = (e) => { docForm.file = e.target.files[0] || null }

    const loadDocsTab = async () => {
      if (docsLoading.value) return
      docsLoading.value = true
      try {
        const [docsRes, policyRes] = await Promise.allSettled([
          axios.get('/me/documents'),
          axios.get('/portal/policy-documents')
        ])
        if (docsRes.status === 'fulfilled') documents.value = docsRes.value.data || []
        if (policyRes.status === 'fulfilled') policyDocs.value = policyRes.value.data || []
      } finally {
        docsLoading.value = false
      }
    }

    const uploadDocument = async () => {
      docUploadError.value = ''
      docUploadSuccess.value = false
      if (!docForm.file) return
      if (docForm.file.size > 5 * 1024 * 1024) { docUploadError.value = 'File must be under 5 MB.'; return }
      docUploading.value = true
      try {
        const fd = new FormData()
        fd.append('file', docForm.file)
        fd.append('document_type', docForm.document_type)
        if (docForm.description) fd.append('description', docForm.description)
        await axios.post('/me/documents', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        docUploadSuccess.value = true
        docForm.document_type = ''; docForm.description = ''; docForm.file = null
        if (fileInput.value) fileInput.value.value = ''
        const { data } = await axios.get('/me/documents')
        documents.value = data || []
      } catch (e) {
        docUploadError.value = e?.response?.data?.detail || 'Upload failed.'
      } finally {
        docUploading.value = false
      }
    }

    const downloadDoc = async (id, name) => {
      try {
        const res = await axios.get(`/me/documents/${id}/download`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.setAttribute('download', name)
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch { alert('Failed to download document.') }
    }

    const downloadPolicyDoc = async (id, name) => {
      try {
        const res = await axios.get(`/portal/policy-documents/${id}/download`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.setAttribute('download', name)
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch { alert('Failed to download document.') }
    }

    // ── Requests tab ──────────────────────────────────────────────────────
    const requestsLoading = ref(false)
    const leaveRequests = ref([])
    const bankingChanges = ref([])
    const pendingBankingChange = computed(() => bankingChanges.value.find(b => b.status === 'pending') || null)
    const bankForm = reactive({ new_bank_name: '', new_account_number: '', new_account_type: '', new_branch_code: '' })
    const bankSubmitting = ref(false)
    const bankChangeError = ref('')
    const bankChangeSuccess = ref(false)

    const loadRequestsTab = async () => {
      if (requestsLoading.value) return
      requestsLoading.value = true
      try {
        const [leaveRes, bankRes] = await Promise.allSettled([
          axios.get('/me/leave'),
          axios.get('/banking-changes/my')
        ])
        if (leaveRes.status === 'fulfilled') leaveRequests.value = leaveRes.value.data?.requests || []
        if (bankRes.status === 'fulfilled') bankingChanges.value = bankRes.value.data || []
      } finally {
        requestsLoading.value = false
      }
    }

    const allRequests = computed(() => {
      const items = []
      leaveRequests.value.forEach(r => items.push({
        ...r, _key: `leave-${r.id}`, _type: 'leave',
        _label: `Leave · ${r.leave_type}`,
        _detail: `${fmtDate(r.start_date)} – ${fmtDate(r.end_date)} (${r.days_requested} day${r.days_requested !== 1 ? 's' : ''})`,
        _date: r.created_at
      }))
      bankingChanges.value.forEach(b => items.push({
        ...b, _key: `bank-${b.id}`, _type: 'banking',
        _label: 'Banking change request',
        _detail: `${b.new_bank_name} · ${b.new_account_number}`,
        _date: b.requested_at
      }))
      return items.sort((a, b) => new Date(b._date) - new Date(a._date))
    })

    const submitBankingChange = async () => {
      bankChangeError.value = ''
      bankChangeSuccess.value = false
      bankSubmitting.value = true
      try {
        await axios.post('/banking-changes', {
          new_bank_name: bankForm.new_bank_name,
          new_account_number: bankForm.new_account_number,
          new_account_type: bankForm.new_account_type || undefined,
          new_branch_code: bankForm.new_branch_code || undefined
        })
        bankChangeSuccess.value = true
        bankForm.new_bank_name = ''; bankForm.new_account_number = ''; bankForm.new_account_type = ''; bankForm.new_branch_code = ''
        const { data } = await axios.get('/banking-changes/my')
        bankingChanges.value = data || []
      } catch (e) {
        bankChangeError.value = e?.response?.data?.detail || 'Failed to submit request.'
      } finally {
        bankSubmitting.value = false
      }
    }

    // ── Announcements tab ─────────────────────────────────────────────────
    const annLoading = ref(false)
    const announcements = ref([])

    const loadAnnouncementsTab = async () => {
      if (annLoading.value) return
      annLoading.value = true
      try {
        const { data } = await axios.get('/portal/announcements')
        announcements.value = data || []
        // Mark all as read
        data.forEach(a => readAnnIds.value.add(a.id))
        _saveReadIds()
      } finally {
        annLoading.value = false
      }
    }

    // ── Lazy tab loading ──────────────────────────────────────────────────
    const loadedTabs = ref(new Set())

    const ensureTabLoaded = (tab) => {
      if (loadedTabs.value.has(tab)) return
      loadedTabs.value.add(tab)
      switch (tab) {
        case 'profile': return loadProfileTab()
        case 'payslips': return loadPayslipsTab()
        case 'documents': return loadDocsTab()
        case 'requests': return loadRequestsTab()
        case 'announcements': return loadAnnouncementsTab()
      }
    }

    watch(activeTab, (tab) => ensureTabLoaded(tab))

    // ── Utils ─────────────────────────────────────────────────────────────
    const fmtMoney = (n) => 'R ' + Number(n || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }
    const statusBadge = (s) => {
      const map = { approved: 'badge-green', paid: 'badge-green', rejected: 'badge-red', cancelled: 'badge-red', pending: 'badge-yellow', processed: 'badge-blue' }
      return map[(s || '').toLowerCase()] || 'badge-gray'
    }

    onMounted(async () => {
      await loadDashboard()
      if (!noProfile.value) ensureTabLoaded(activeTab.value)
    })

    return {
      loading, noProfile, activeTab, tabs, tabLabel, setTab,
      dash, avatarInitials, unreadAnnouncementCount, totalPendingCount,
      completingTask, completeTask,
      // Profile
      profileLoading, profileData, profileForm, profileSaving, profileSaveError, profileSaveSuccess,
      picUploading, picError, onPicChange,
      emergencyContacts, ecForm, ecSaving, ecError, editEC, cancelECEdit, saveEC, deleteEC,
      saveProfile,
      // Payslips
      payslipsLoading, payslips, page, pageSize, totalPages, pagedPayslips, salaryHistory,
      prevPage, nextPage, downloading, downloadPayslip,
      // Documents
      docsLoading, documents, policyDocs, fileInput, docForm,
      docUploading, docUploadError, docUploadSuccess, onFileChange, uploadDocument, downloadDoc, downloadPolicyDoc,
      // Requests
      requestsLoading, leaveRequests, bankingChanges, allRequests, pendingBankingChange,
      bankForm, bankSubmitting, bankChangeError, bankChangeSuccess, submitBankingChange,
      // Announcements
      annLoading, announcements,
      fmtMoney, fmtDate, statusBadge
    }
  }
}
</script>

<style scoped>
.portal-content {
  padding: 24px;
  max-width: 1100px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 500; color: var(--color-text-base); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.loading-state { display: flex; align-items: center; gap: 10px; color: var(--color-text-muted); font-size: 13px; }

.spinner {
  width: 18px; height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px;
}

.warn-card {
  display: flex; align-items: flex-start; gap: 14px;
  background: #fffbeb; border-color: #fde68a; padding: 16px 20px;
}
.warn-icon { width: 22px; height: 22px; color: #d97706; flex-shrink: 0; margin-top: 2px; }
.warn-title { font-size: 13px; font-weight: 600; color: #92400e; margin: 0 0 4px; }
.warn-sub { font-size: 12px; color: #92400e; margin: 0; }

/* ── Tab bar ───────────────────────────────────────────────────────────── */
.tab-bar {
  display: flex; gap: 4px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0;
  flex-wrap: wrap;
}
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  font-size: 13px; font-weight: 500;
  color: var(--color-text-muted);
  background: none; border: none; border-bottom: 2px solid transparent;
  cursor: pointer; transition: color 0.15s, border-color 0.15s;
  margin-bottom: -1px;
}
.tab-btn:hover { color: var(--color-text-base); }
.tab-btn.is-active { color: var(--color-accent); border-bottom-color: var(--color-accent); }
.tab-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  border-radius: 9px; font-size: 10px; font-weight: 700;
  background: var(--color-accent); color: #fff;
}

/* ── Welcome card ──────────────────────────────────────────────────────── */
.welcome-card { display: flex; align-items: center; gap: 20px; }
.welcome-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--color-accent); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 700; flex-shrink: 0;
}
.welcome-name { font-size: 16px; font-weight: 600; color: var(--color-text-base); margin: 0 0 2px; }
.welcome-position { font-size: 12px; color: var(--color-text-muted); margin: 0 0 8px; }
.profile-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.meta-item { display: flex; gap: 4px; font-size: 12px; }
.meta-label { color: var(--color-text-muted); }
.meta-value { color: var(--color-text-base); font-weight: 500; }
.meta-sep { color: var(--color-border); }

/* ── Cards grid ────────────────────────────────────────────────────────── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.dash-card { display: flex; flex-direction: column; gap: 12px; padding: 18px; }
.dash-card-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--color-text-muted); margin: 0;
  display: flex; align-items: center; gap: 8px;
}
.dash-empty { font-size: 12px; color: var(--color-text-muted); }
.dash-link { background: none; border: none; padding: 0; font-size: 12px; color: var(--color-accent); cursor: pointer; text-align: left; }
.dash-link:hover { text-decoration: underline; }
.dash-unread-dot { font-size: 10px; font-weight: 700; background: var(--color-accent); color: #fff; padding: 1px 6px; border-radius: 8px; }

/* Leave list */
.leave-list { display: flex; flex-direction: column; gap: 10px; }
.leave-item { display: flex; flex-direction: column; gap: 4px; }
.leave-item-header { display: flex; justify-content: space-between; align-items: center; }
.leave-type { font-size: 12px; font-weight: 600; color: var(--color-text-base); }
.leave-stat { font-size: 11px; color: var(--color-text-muted); }
.leave-bar-track { height: 5px; background: var(--color-border); border-radius: 3px; overflow: hidden; }
.leave-bar-fill { height: 100%; background: #15803d; border-radius: 3px; transition: width 0.4s; }

/* Recent payslips */
.recent-slips { display: flex; flex-direction: column; gap: 8px; }
.recent-slip-row { display: flex; align-items: center; gap: 8px; }
.recent-slip-period { font-size: 12px; color: var(--color-text-base); flex: 1; }
.recent-slip-net { font-size: 12px; font-weight: 600; color: var(--color-text-base); white-space: nowrap; }

/* Pending */
.pending-list { display: flex; flex-direction: column; gap: 10px; }
.pending-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; border-radius: 6px; padding: 4px 2px; }
.pending-item:hover { background: var(--color-bg-page); }
.pending-label { font-size: 12.5px; color: var(--color-text-base); }
.pending-count {
  min-width: 28px; height: 22px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.count-yellow { background: #fef9c3; color: #854d0e; }
.count-zero { background: #dcfce7; color: #15803d; }

/* Holidays */
.holiday-list { display: flex; flex-direction: column; gap: 10px; }
.holiday-item { display: flex; align-items: center; gap: 12px; }
.holiday-days-away {
  min-width: 44px; text-align: center;
  font-size: 11px; font-weight: 700;
  color: var(--color-accent); background: color-mix(in srgb, var(--color-accent) 10%, transparent);
  padding: 3px 6px; border-radius: 6px;
}
.holiday-name { font-size: 12px; font-weight: 600; color: var(--color-text-base); margin: 0 0 1px; }
.holiday-date { font-size: 11px; color: var(--color-text-muted); margin: 0; }

/* Announcement previews */
.ann-list { display: flex; flex-direction: column; gap: 10px; }
.ann-item { border-left: 3px solid var(--color-accent); padding-left: 10px; }
.ann-title { font-size: 12px; font-weight: 600; color: var(--color-text-base); margin: 0 0 2px; }
.ann-preview { font-size: 11.5px; color: var(--color-text-muted); margin: 0; }

/* Tasks */
.task-list { display: flex; flex-direction: column; gap: 8px; }
.task-item { display: flex; align-items: flex-start; gap: 10px; }
.task-check {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid var(--color-border);
  background: none; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, border-color 0.15s;
}
.task-check:hover { border-color: #15803d; background: #dcfce7; }
.task-check svg { width: 12px; height: 12px; color: #15803d; }
.task-title { font-size: 12.5px; color: var(--color-text-base); margin: 0 0 1px; }
.task-due { font-size: 11px; color: var(--color-text-muted); margin: 0; }

/* ── Profile tab ───────────────────────────────────────────────────────── */
.section { display: flex; flex-direction: column; gap: 10px; }
.section-title {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-text-muted); margin: 0;
}
.profile-pic-card { display: flex; align-items: center; gap: 20px; }
.profile-avatar-lg {
  width: 72px; height: 72px; border-radius: 50%;
  background: var(--color-accent); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 700; flex-shrink: 0; overflow: hidden;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.profile-pic-label { font-size: 12px; color: var(--color-text-muted); margin: 0 0 8px; }
.profile-pic-actions { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.hidden-file-input { display: none; }

.readonly-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.readonly-item { display: flex; flex-direction: column; gap: 3px; }
.readonly-label { font-size: 11px; font-weight: 500; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.readonly-val { font-size: 13px; color: var(--color-text-base); font-weight: 500; }

/* Emergency contacts */
.ec-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--color-border); padding-bottom: 16px; }
.ec-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ec-info { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; flex: 1; }
.ec-name { font-size: 13px; font-weight: 600; color: var(--color-text-base); }
.ec-rel { font-size: 12px; color: var(--color-text-muted); }
.ec-phone { font-size: 12px; color: var(--color-text-base); }
.ec-actions { display: flex; gap: 6px; flex-shrink: 0; }
.ec-form-wrap { padding-top: 4px; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--color-text-base); cursor: pointer; }

/* ── Payslips tab ──────────────────────────────────────────────────────── */
.net-pay-cell { font-weight: 600; color: var(--color-text-base); }
.empty-state-card { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px 20px; }
.empty-icon { width: 40px; height: 40px; color: var(--color-text-muted); }
.empty-state { font-size: 13px; color: var(--color-text-muted); text-align: center; padding: 24px 0; margin: 0; }

/* ── Documents tab ─────────────────────────────────────────────────────── */
.doc-list { display: flex; flex-direction: column; gap: 8px; }
.doc-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--color-border); }
.doc-row:last-child { border-bottom: none; }
.doc-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.doc-name { font-size: 13px; font-weight: 500; color: var(--color-text-base); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-type { font-size: 11px; color: var(--color-text-muted); }
.doc-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.rejection-reason { font-size: 11.5px; color: #b91c1c; font-style: italic; max-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ── Requests tab ──────────────────────────────────────────────────────── */
.timeline { display: flex; flex-direction: column; }
.timeline-item { display: flex; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--color-border); }
.timeline-item:last-child { border-bottom: none; }
.tl-icon-wrap { flex-shrink: 0; padding-top: 2px; }
.tl-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.tl-icon svg { width: 16px; height: 16px; }
.tl-icon.leave { background: #dbeafe; color: #1d4ed8; }
.tl-icon.document { background: #f3e8ff; color: #7c3aed; }
.tl-icon.banking { background: #dcfce7; color: #15803d; }
.tl-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.tl-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tl-label { font-size: 13px; font-weight: 600; color: var(--color-text-base); }
.tl-detail { font-size: 12px; color: var(--color-text-muted); margin: 0; }
.tl-date { font-size: 11px; color: var(--color-text-muted); margin: 0; }
.tl-reason { font-size: 11.5px; color: #b91c1c; margin: 0; font-style: italic; }

.banking-current { margin-bottom: 4px; }
.banking-label { font-size: 11.5px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 10px; }
.banking-fields { display: flex; gap: 20px; flex-wrap: wrap; }
.banking-field { display: flex; gap: 6px; font-size: 13px; }
.banking-divider { height: 1px; background: var(--color-border); margin: 16px 0; }
.pending-change-banner { display: flex; align-items: flex-start; gap: 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 16px; margin-top: 12px; }
.pending-icon { width: 20px; height: 20px; color: #d97706; flex-shrink: 0; margin-top: 2px; }
.pending-title { font-size: 13px; font-weight: 600; color: #92400e; margin: 0 0 2px; }
.pending-sub { font-size: 12px; color: #92400e; margin: 0; }

/* ── Announcements tab ─────────────────────────────────────────────────── */
.ann-full-list { display: flex; flex-direction: column; gap: 14px; }
.ann-full-card { display: flex; flex-direction: column; gap: 10px; }
.ann-full-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.ann-full-title { font-size: 14px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.ann-full-date { font-size: 11px; color: var(--color-text-muted); white-space: nowrap; flex-shrink: 0; }
.ann-full-body { font-size: 13px; color: var(--color-text-base); line-height: 1.6; margin: 0; white-space: pre-wrap; }

/* ── Shared ────────────────────────────────────────────────────────────── */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  text-align: left; padding: 10px 14px;
  font-size: 11px; font-weight: 600; color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border); white-space: nowrap;
}
.data-table td { padding: 10px 14px; color: var(--color-text-base); border-bottom: 1px solid var(--color-border); }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.badge { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.btn-sm { padding: 4px 12px; font-size: 12px; }
.pagination { display: flex; align-items: center; gap: 12px; padding: 14px 14px 0; border-top: 1px solid var(--color-border); margin-top: 4px; }
.page-info { font-size: 12px; color: var(--color-text-muted); }
.page-btn { padding: 4px 12px; font-size: 12px; }

.form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }
.file-input { padding: 5px 8px; }
.form-actions-row { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 12px; }
.form-error { font-size: 12px; color: #dc2626; }
.form-success { font-size: 12px; color: #15803d; }
.success-banner { margin-top: 10px; padding: 9px 14px; background: #dcfce7; border: 1px solid #86efac; border-radius: 7px; font-size: 12.5px; color: #15803d; }

@media (max-width: 900px) {
  .cards-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .cards-grid { grid-template-columns: 1fr; }
  .welcome-card { flex-direction: column; align-items: flex-start; }
  .form-grid-2 { grid-template-columns: 1fr; }
  .form-grid-3 { grid-template-columns: 1fr; }
  .banking-fields { flex-direction: column; gap: 6px; }
  .tab-bar { gap: 2px; }
  .tab-btn { padding: 6px 10px; font-size: 12px; }
}
</style>

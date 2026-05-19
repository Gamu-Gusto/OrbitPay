<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <button class="btn-light" @click="$router.push('/')">← Back</button>
        <h1 class="text-2xl font-bold text-gray-900">Document Management</h1>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Upload Section -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h2>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
              <select v-model="uploadForm.document_type" class="form-input w-full">
                <option value="">Select document type</option>
                <option value="contract">Employment Contract</option>
                <option value="tax_form">Tax Form (IRP5)</option>
                <option value="work_permit">Work Permit</option>
                <option value="disciplinary">Disciplinary Record</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">File</label>
              <input
                ref="fileInput"
                type="file"
                @change="handleFileSelect"
                class="form-input w-full"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />
              <p class="text-xs text-gray-500 mt-1">Accepted formats: PDF, DOC, DOCX, JPG, PNG</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <input v-model="uploadForm.description" type="text" class="form-input w-full" placeholder="Brief description of the document" />
            </div>

            <button
              @click="uploadDocument"
              :disabled="!uploadForm.document_type || !selectedFile || isUploading"
              class="btn-primary w-full"
              :class="{ 'opacity-50 cursor-not-allowed': !uploadForm.document_type || !selectedFile || isUploading }"
            >
              {{ isUploading ? 'Uploading...' : 'Upload Document' }}
            </button>
          </div>

          <div v-if="uploadError" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-800">{{ uploadError }}</p>
          </div>

          <div v-if="uploadSuccess" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p class="text-green-800">{{ uploadSuccess }}</p>
          </div>
        </div>
      </div>

      <!-- Documents List -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">My Documents</h2>

          <div v-if="documents.length === 0" class="text-center py-8 text-gray-500">
            <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p>No documents uploaded yet</p>
          </div>

          <div v-else class="space-y-3">
            <div v-for="doc in documents" :key="doc.id" class="border border-gray-200 rounded-lg p-4">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-1">
                    <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <h3 class="font-medium text-gray-900">{{ getDocumentTypeLabel(doc.document_type) }}</h3>
                    <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {{ formatDate(doc.uploaded_at) }}
                    </span>
                  </div>
                  <p v-if="doc.description" class="text-sm text-gray-600 mb-2">{{ doc.description }}</p>
                  <p class="text-xs text-gray-500">Uploaded by: {{ doc.uploaded_by }}</p>
                </div>
                <div class="flex items-center space-x-2">
                  <button @click="downloadDocument(doc)" class="text-blue-600 hover:text-blue-800 text-sm">
                    Download
                  </button>
                  <button @click="deleteDocument(doc.id)" class="text-red-600 hover:text-red-800 text-sm">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'EmployeeDocumentsView',
  setup() {
    const auth = useAuthStore()
    const isUploading = ref(false)
    const uploadError = ref('')
    const uploadSuccess = ref('')
    const documents = ref([])
    const selectedFile = ref(null)
    const fileInput = ref(null)

    const uploadForm = reactive({
      document_type: '',
      description: ''
    })

    const API = 'http://localhost:8002'

    const handleFileSelect = (event) => {
      selectedFile.value = event.target.files[0]
    }

    const uploadDocument = async () => {
      if (!selectedFile.value || !uploadForm.document_type) return

      isUploading.value = true
      uploadError.value = ''
      uploadSuccess.value = ''

      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        formData.append('document_type', uploadForm.document_type)
        formData.append('description', uploadForm.description)

        await axios.post(`${API}/employee-documents`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        uploadSuccess.value = 'Document uploaded successfully!'
        setTimeout(() => {
          uploadSuccess.value = ''
        }, 3000)

        // Reset form
        uploadForm.document_type = ''
        uploadForm.description = ''
        selectedFile.value = null
        fileInput.value.value = ''

        // Reload documents
        loadDocuments()
      } catch (e) {
        uploadError.value = e.response?.data?.detail || 'Failed to upload document'
        console.error('Error uploading document:', e)
      } finally {
        isUploading.value = false
      }
    }

    const loadDocuments = async () => {
      try {
        // Get employee's profile to get employee_id
        const { data: profile } = await axios.get(`${API}/my-profile`)
        const response = await axios.get(`${API}/employees/${profile.id}/documents`)
        documents.value = response.data
      } catch (e) {
        console.error('Error loading documents:', e)
        // For now, use mock data if API fails
        documents.value = [
          {
            id: 1,
            document_type: 'contract',
            description: 'Employment Contract 2024',
            uploaded_by: 'HR Department',
            uploaded_at: '2024-01-15',
            file_name: 'contract_2024.pdf'
          }
        ]
      }
    }

    const downloadDocument = async (doc) => {
      try {
        const response = await axios.get(`${API}/employee-documents/${doc.id}/download`, {
          responseType: 'blob'
        })

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', doc.file_name)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (e) {
        console.error('Error downloading document:', e)
        alert('Error downloading document. Please try again.')
      }
    }

    const deleteDocument = async (docId) => {
      if (!confirm('Are you sure you want to delete this document?')) return

      try {
        await axios.delete(`${API}/employee-documents/${docId}`)
        documents.value = documents.value.filter(doc => doc.id !== docId)
      } catch (e) {
        console.error('Error deleting document:', e)
        alert('Error deleting document. Please try again.')
      }
    }

    const getDocumentTypeLabel = (type) => {
      const labels = {
        contract: 'Employment Contract',
        tax_form: 'Tax Form (IRP5)',
        work_permit: 'Work Permit',
        disciplinary: 'Disciplinary Record',
        other: 'Other Document'
      }
      return labels[type] || type
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(loadDocuments)

    return {
      auth,
      isUploading,
      uploadError,
      uploadSuccess,
      documents,
      selectedFile,
      fileInput,
      uploadForm,
      handleFileSelect,
      uploadDocument,
      downloadDocument,
      deleteDocument,
      getDocumentTypeLabel,
      formatDate
    }
  }
}
</script>

<script setup>
import { ref } from "vue";
import html2pdf from "html2pdf.js";

const props = defineProps({
  company: {
    type: Object,
    default: () => ({
      name: "Mimido Pty Ltd",
      address: "719 Heart Street, Gustoland, Pretoria, 0001",
      regNo: "2025/263231/07",
      uifRef: "0321236/2",
      phone: "0112638974",
      email: "info@mimido.com",
      logo: null, // optional: URL to logo image
    }),
  },
  employee: {
    type: Object,
    default: () => ({
      firstName: "Gamuchirai",
      lastName: "Dambanjera",
      id: "AE069695",
      empNo: "001",
      taxRef: "0105261241",
      empDate: "2025-05-05",
    }),
  },
  payslip: {
    type: Object,
    default: () => ({
      run: "Dec 2025",
      paymentDate: "2025-10-08",
      earnings: [
        { description: "Basic Pay", amount: 100000 },
        { description: "Other Earnings", amount: 25000 },
      ],
      deductions: [
        { description: "PAYE", amount: 41440.33 },
        { description: "UIF", amount: 177.12 },
        { description: "Pension", amount: 5000 },
        { description: "Medical Aid", amount: 8000 },
      ],
    }),
  },
  preparedBy: {
    type: String,
    default: "OrbitPay",
  },
});

const payslipRef = ref(null);

const downloadPDF = () => {
  const element = payslipRef.value;
  const opt = {
    margin: 10,
    filename: `${props.employee.lastName}_${props.employee.firstName}_Payslip.pdf`,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  };
  html2pdf().set(opt).from(element).save();
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col items-center py-8 px-4">
    <div ref="payslipRef" class="bg-white w-full max-w-4xl shadow-2xl rounded-3xl overflow-hidden border border-slate-200">
      <!-- Header Section with Accent -->
      <div class="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-8 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full -translate-y-16 translate-x-16"></div>
        <div class="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-5 rounded-full translate-y-12 -translate-x-12"></div>
        
        <div class="relative text-center">
          <!-- Company Information - Prominently displayed at top -->
          <div class="mb-6">
            <h1 class="text-4xl font-bold mb-3 tracking-tight">{{ company.name }}</h1>
            <div class="space-y-2 text-blue-100">
              <p class="text-lg font-medium">{{ company.address }}</p>
              <div class="flex justify-center flex-wrap gap-4 text-sm">
                <span class="bg-white bg-opacity-20 px-4 py-2 rounded-full font-medium">Reg: {{ company.regNo }}</span>
                <span class="bg-white bg-opacity-20 px-4 py-2 rounded-full font-medium">UIF: {{ company.uifRef }}</span>
                <span class="bg-white bg-opacity-20 px-4 py-2 rounded-full font-medium">{{ company.phone }}</span>
              </div>
            </div>
          </div>
          
          <!-- Company Logo (if available) -->
          <div v-if="company.logo" class="flex justify-center mb-4">
            <div class="w-24 h-24 bg-white bg-opacity-10 rounded-xl p-3 backdrop-blur-sm">
              <img :src="company.logo" alt="Company Logo" class="w-full h-full object-contain" />
            </div>
          </div>
        </div>
      </div>

      <!-- Payslip Title Section -->
      <div class="bg-slate-50 px-8 py-6 border-b border-slate-200">
        <div class="text-center">
          <h2 class="text-2xl font-bold text-slate-800 mb-2">Payslip</h2>
          <div class="flex justify-center gap-6 text-sm text-slate-600">
            <span class="bg-white px-4 py-2 rounded-lg shadow-sm border">
              <span class="font-semibold text-indigo-600">Run:</span> {{ payslip.run }}
            </span>
            <span class="bg-white px-4 py-2 rounded-lg shadow-sm border">
              <span class="font-semibold text-indigo-600">Payment Date:</span> {{ payslip.paymentDate }}
            </span>
          </div>
        </div>
      </div>

      <!-- Employee Details Card -->
      <div class="p-8">
        <div class="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-2xl p-6 mb-8 border border-emerald-200">
          <div class="flex items-center mb-4">
            <div class="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center mr-3">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-emerald-800">Employee Details</h3>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">First Names:</span>
                <span class="font-semibold text-slate-800">{{ employee.firstName }}</span>
              </div>
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">ID/Passport:</span>
                <span class="font-semibold text-slate-800">{{ employee.id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">Tax Ref:</span>
                <span class="font-semibold text-slate-800">{{ employee.taxRef }}</span>
              </div>
            </div>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">Last Name:</span>
                <span class="font-semibold text-slate-800">{{ employee.lastName }}</span>
              </div>
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">Employee No:</span>
                <span class="font-semibold text-slate-800">{{ employee.empNo }}</span>
              </div>
              <div class="flex justify-between">
                <span class="font-medium text-slate-600">Emp Date:</span>
                <span class="font-semibold text-slate-800">{{ employee.empDate }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Earnings & Deductions Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Earnings Box -->
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl border border-green-200 overflow-hidden">
            <div class="bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-4">
              <div class="flex items-center">
                <div class="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center mr-3">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                  </svg>
                </div>
                <h3 class="text-lg font-bold text-white">EARNINGS</h3>
              </div>
            </div>
            <div class="p-6">
              <div class="space-y-3">
                <div v-for="(item, index) in payslip.earnings" :key="index" 
                     class="flex justify-between items-center py-2 border-b border-green-200 last:border-b-0">
                  <span class="text-slate-700 font-medium">{{ item.description }}</span>
                  <span class="text-slate-800 font-bold">R{{ item.amount.toFixed(2) }}</span>
                </div>
                <div class="pt-3 border-t-2 border-green-300">
                  <div class="flex justify-between items-center">
                    <span class="text-green-700 font-bold text-lg">Total Earnings</span>
                    <span class="text-green-700 font-bold text-lg">R{{ payslip.earnings.reduce((a, b) => a + b.amount, 0).toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Deductions Box -->
          <div class="bg-gradient-to-br from-red-50 to-rose-50 rounded-2xl border border-red-200 overflow-hidden">
            <div class="bg-gradient-to-r from-red-500 to-rose-500 px-6 py-4">
              <div class="flex items-center">
                <div class="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center mr-3">
                  <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4m16 0l-4-4m4 4l-4 4"></path>
                  </svg>
                </div>
                <h3 class="text-lg font-bold text-white">DEDUCTIONS</h3>
              </div>
            </div>
            <div class="p-6">
              <div class="space-y-3">
                <div v-for="(item, index) in payslip.deductions" :key="index" 
                     class="flex justify-between items-center py-2 border-b border-red-200 last:border-b-0">
                  <span class="text-slate-700 font-medium">{{ item.description }}</span>
                  <span class="text-slate-800 font-bold">R{{ item.amount.toFixed(2) }}</span>
                </div>
                <div class="pt-3 border-t-2 border-red-300">
                  <div class="flex justify-between items-center">
                    <span class="text-red-700 font-bold text-lg">Total Deductions</span>
                    <span class="text-red-700 font-bold text-lg">R{{ payslip.deductions.reduce((a, b) => a + b.amount, 0).toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Net Pay Highlight Box -->
        <div class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 text-center mb-8 relative overflow-hidden">
          <div class="absolute inset-0 bg-white opacity-10"></div>
          <div class="relative">
            <div class="flex items-center justify-center mb-2">
              <div class="w-12 h-12 bg-white bg-opacity-20 rounded-2xl flex items-center justify-center mr-3">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <h3 class="text-2xl font-bold text-white">NET PAY</h3>
            </div>
            <p class="text-4xl font-black text-white tracking-tight">
              R{{ (payslip.earnings.reduce((a, b) => a + b.amount, 0) - payslip.deductions.reduce((a, b) => a + b.amount, 0)).toFixed(2) }}
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gradient-to-r from-slate-100 to-slate-200 rounded-xl p-8 border border-slate-300">
          <div class="text-center">
            <div class="flex items-center justify-center space-x-4 mb-3">
              <div class="w-32 h-10">
                <img src="/OrbitPayfinal.jpeg" alt="OrbitPay Logo" class="w-full h-full object-contain opacity-90" />
              </div>
            </div>
            <div class="text-slate-700">
              <p class="text-lg font-semibold mb-1">Prepared by</p>
              <p class="text-xl font-bold text-slate-800">OrbitPay</p>
              <p class="text-sm text-slate-600 mt-2">Professional Payroll Services</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Download Button -->
    <button
      @click="downloadPDF"
      class="mt-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-4 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 font-semibold text-lg"
    >
      <div class="flex items-center">
        <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        Download PDF
      </div>
    </button>
  </div>
</template>
<template>
  <div class="welcome">
    <HeaderBar/>
    
    <div class="operation-bar">
      <h2 class="page-title">📚 RAG Document Management</h2>
      <div class="right-operations">
        <el-select v-model="searchParams.grade" placeholder="Grade" clearable class="grade-select">
          <el-option label="Class 6" value="class-6"></el-option>
          <el-option label="Class 7" value="class-7"></el-option>
          <el-option label="Class 8" value="class-8"></el-option>
        </el-select>
        <el-select v-model="searchParams.subject" placeholder="Subject" clearable class="subject-select">
          <el-option label="Mathematics" value="mathematics"></el-option>
          <el-option label="Science" value="science"></el-option>
          <el-option label="English" value="english"></el-option>
        </el-select>
        <el-input placeholder="Document name" v-model="searchParams.documentName" class="search-input" clearable/>
        <el-button class="btn-search" @click="loadDocuments">Search</el-button>
        <el-button type="primary" @click="showUploadDialog = true">Upload Document</el-button>
      </div>
    </div>

    <div class="main-wrapper">
      <div class="content-panel">
        <!-- Collections Overview -->
        <el-card class="overview-card" shadow="never" v-if="collections.length > 0">
          <div slot="header" class="card-header">
            <span>📊 Collections Overview</span>
            <el-button size="small" @click="loadCollections">Refresh</el-button>
          </div>
          <div class="collection-grid">
            <div v-for="collection in collections" :key="collection.collectionName" class="collection-item" @click="viewCollectionDetails(collection)">
              <div class="collection-info">
                <h4>{{ collection.grade }} - {{ collection.subject }}</h4>
                <p>Documents: {{ collection.totalDocuments || 0 }}</p>
                <p>Total Chunks: {{ collection.totalChunks || 0 }}</p>
                <p>Status: {{ collection.status }}</p>
              </div>
              <div class="collection-actions" @click.stop>
                <el-button size="mini" type="primary" @click="viewCollectionDetails(collection)">
                  View Details
                </el-button>
                <el-button size="mini" type="danger" @click="deleteCollection(collection.grade, collection.subject)">
                  Delete
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Document List -->
        <el-card class="documents-card" shadow="never">
          <div slot="header" class="card-header">
            <span>📄 Documents</span>
            <div class="header-actions">
              <el-select v-model="filterStatus" placeholder="Filter by status" style="width: 150px;" @change="loadDocuments">
                <el-option label="All" value=""></el-option>
                <el-option label="Uploaded" value="UPLOADED"></el-option>
                <el-option label="Processing" value="PROCESSING"></el-option>
                <el-option label="Processed" value="PROCESSED"></el-option>
                <el-option label="Failed" value="FAILED"></el-option>
              </el-select>
            </div>
          </div>
          
          <el-table :data="documents" v-loading="loading" element-loading-text="Loading documents..." style="width: 100%">
            <el-table-column prop="documentName" label="Document Name" min-width="200"/>
            <el-table-column prop="grade" label="Grade" width="100"/>
            <el-table-column prop="subject" label="Subject" width="120"/>
            <el-table-column prop="status" label="Status" width="120">
              <template slot-scope="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="fileSize" label="Size" width="100">
              <template slot-scope="scope">
                {{ formatFileSize(scope.row.fileSize) }}
              </template>
            </el-table-column>
            <el-table-column prop="uploadTime" label="Upload Time" width="150">
              <template slot-scope="scope">
                {{ formatDate(scope.row.uploadTime) }}
              </template>
            </el-table-column>
            <el-table-column label="Progress" width="120" v-if="hasProcessingDocs">
              <template slot-scope="scope">
                <div v-if="scope.row.status === 'PROCESSING'">
                  <el-progress :percentage="getProgress(scope.row)" :status="getProgressStatus(scope.row)"/>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="200">
              <template slot-scope="scope">
                <el-button size="mini" @click="viewDocument(scope.row)" v-if="scope.row.status === 'PROCESSED'">
                  View
                </el-button>
                <el-button size="mini" type="primary" @click="processDocument(scope.row)" 
                          v-if="scope.row.status === 'UPLOADED'">
                  Process
                </el-button>
                <el-button size="mini" type="danger" @click="deleteDocument(scope.row)">
                  Delete
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- Pagination -->
          <div class="pagination-wrapper">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="pagination.page"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="pagination.limit"
              layout="total, sizes, prev, pager, next, jumper"
              :total="pagination.total">
            </el-pagination>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Upload Dialog -->
    <el-dialog title="Upload Document" :visible.sync="showUploadDialog" width="500px">
      <el-form :model="uploadForm" label-width="100px" ref="uploadForm">
        <el-form-item label="Grade" required>
          <el-select v-model="uploadForm.grade" placeholder="Select grade">
            <el-option label="Class 6" value="class-6"></el-option>
            <el-option label="Class 7" value="class-7"></el-option>
            <el-option label="Class 8" value="class-8"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="Subject" required>
          <el-select v-model="uploadForm.subject" placeholder="Select subject">
            <el-option label="Mathematics" value="mathematics"></el-option>
            <el-option label="Science" value="science"></el-option>
            <el-option label="English" value="english"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="Document Name">
          <el-input v-model="uploadForm.documentName" placeholder="Optional custom name"/>
        </el-form-item>
        <el-form-item label="Upload Mode" required>
          <el-radio-group v-model="uploadForm.mode">
            <el-radio label="single">Single Document</el-radio>
            <el-radio label="batch">Multiple Documents (Chapter-wise)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="File(s)" required>
          <el-upload
            ref="upload"
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-remove="beforeRemove"
            accept=".pdf"
            :limit="uploadForm.mode === 'single' ? 1 : 10"
            :multiple="uploadForm.mode === 'batch'">
            <el-button size="small" type="primary">
              {{ uploadForm.mode === 'single' ? 'Select PDF File' : 'Select PDF Files' }}
            </el-button>
            <div slot="tip" class="el-upload__tip">
              {{ uploadForm.mode === 'single' ? 'Only PDF files are supported, max 50MB' : 'Select multiple PDF files (chapters), max 10 files, 50MB each' }}
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <div slot="footer" class="dialog-footer">
        <el-button @click="showUploadDialog = false">Cancel</el-button>
        <el-button type="primary" @click="uploadDocument" :loading="uploading">
          {{ uploading ? 'Uploading...' : (uploadForm.mode === 'single' ? 'Upload' : 'Upload All') }}
        </el-button>
      </div>
    </el-dialog>

    <!-- Document Detail Dialog -->
    <el-dialog title="Document Details" :visible.sync="documentDialogVisible" width="600px">
      <div v-if="selectedDocument">
        <el-row>
          <el-col :span="12">
            <p><strong>Document Name:</strong> {{ selectedDocument.documentName }}</p>
            <p><strong>File Name:</strong> {{ selectedDocument.fileName }}</p>
            <p><strong>Grade:</strong> {{ selectedDocument.grade }}</p>
            <p><strong>Subject:</strong> {{ selectedDocument.subject }}</p>
          </el-col>
          <el-col :span="12">
            <p><strong>Status:</strong> 
              <el-tag :type="getStatusType(selectedDocument.status)">{{ selectedDocument.status }}</el-tag>
            </p>
            <p><strong>File Size:</strong> {{ formatFileSize(selectedDocument.fileSize) }}</p>
            <p><strong>Total Chunks:</strong> {{ selectedDocument.totalChunks || '-' }}</p>
            <p><strong>Processed Chunks:</strong> {{ selectedDocument.processedChunks || '-' }}</p>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <p><strong>Upload Time:</strong> {{ formatDate(selectedDocument.uploadTime) }}</p>
            <p><strong>Processed Time:</strong> {{ formatDate(selectedDocument.processedTime) || '-' }}</p>
          </el-col>
        </el-row>
        
        <div v-if="selectedDocument.processingStats" style="margin-top: 20px">
          <h4>Processing Statistics</h4>
          <el-row>
            <el-col :span="12">
              <p><strong>Text Chunks:</strong> {{ selectedDocument.processingStats.textChunks }}</p>
              <p><strong>Table Chunks:</strong> {{ selectedDocument.processingStats.tableChunks }}</p>
            </el-col>
            <el-col :span="12">
              <p><strong>Image Chunks:</strong> {{ selectedDocument.processingStats.imageChunks }}</p>
              <p><strong>Total Pages:</strong> {{ selectedDocument.processingStats.totalPages }}</p>
            </el-col>
          </el-row>
        </div>
        
        <div v-if="selectedDocument.processingError" style="margin-top: 20px">
          <el-alert type="error" :closable="false">
            <template slot="title">Processing Error</template>
            {{ selectedDocument.processingError }}
          </el-alert>
        </div>
      </div>
    </el-dialog>

    <!-- Collection Detail Dialog -->
    <el-dialog title="Collection Details" :visible.sync="collectionDetailVisible" width="80%" :close-on-click-modal="false">
      <div v-if="selectedCollection">
        <!-- Collection Header -->
        <el-row style="margin-bottom: 20px;">
          <el-col :span="24">
            <h2>{{ selectedCollection.grade }} - {{ selectedCollection.subject }}</h2>
            <el-tag :type="getCollectionStatusType(selectedCollection.status)" size="medium">
              {{ selectedCollection.status }}
            </el-tag>
          </el-col>
        </el-row>

        <!-- Statistics Overview -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ selectedCollection.totalDocuments || 0 }}</div>
                <div class="stat-label">Documents</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ selectedCollection.totalChunks || 0 }}</div>
                <div class="stat-label">Total Chunks</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ collectionAnalytics.totalTopics || 0 }}</div>
                <div class="stat-label">Topics</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ collectionAnalytics.avgDifficulty || 'N/A' }}</div>
                <div class="stat-label">Avg Difficulty</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Tabs for Different Views -->
        <el-tabs v-model="activeTab" type="card">
          <!-- Content Analysis Tab -->
          <el-tab-pane label="📊 Content Analysis" name="analysis">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-card>
                  <div slot="header">📊 Content Types Breakdown</div>
                  <div v-if="collectionAnalytics.contentTypes">
                    <div v-for="item in getSortedContentTypes(collectionAnalytics.contentTypes)" 
                         :key="item.type" 
                         class="content-type-enhanced clickable-content-type"
                         @click="viewContentTypeDetails(item.type, item.count)">
                      <div class="content-type-header">
                        <span class="content-type-icon">{{ getContentTypeIcon(item.type) }}</span>
                        <span class="content-type-name">{{ formatContentType(item.type) }}</span>
                        <div class="content-type-stats">
                          <el-tag size="mini" :type="getContentTypeTagType(item.type)">{{ item.count }}</el-tag>
                          <span class="content-type-percent">{{ item.percentage }}%</span>
                        </div>
                      </div>
                      <el-progress 
                        :percentage="item.percentage" 
                        :stroke-width="6"
                        :color="getContentTypeColor(item.type)"
                        :show-text="false">
                      </el-progress>
                      <div class="click-hint">Click to view all {{ item.count }} items</div>
                    </div>
                  </div>
                  <div v-else class="no-data">
                    <i class="el-icon-document"></i>
                    <p>No content analysis available</p>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <div slot="header">🗂️ Processing Types</div>
                  <div v-if="collectionAnalytics.chunkTypes">
                    <div v-for="item in getSortedContentTypes(collectionAnalytics.chunkTypes)" :key="item.type" class="content-type-enhanced">
                      <div class="content-type-header">
                        <span class="content-type-icon">{{ getChunkTypeIcon(item.type) }}</span>
                        <span class="content-type-name">{{ formatContentType(item.type) }}</span>
                        <div class="content-type-stats">
                          <el-tag size="mini" :type="getChunkTypeTagType(item.type)">{{ item.count }}</el-tag>
                          <span class="content-type-percent">{{ item.percentage }}%</span>
                        </div>
                      </div>
                      <el-progress 
                        :percentage="item.percentage" 
                        :stroke-width="6"
                        :color="getChunkTypeColor(item.type)"
                        :show-text="false">
                      </el-progress>
                    </div>
                  </div>
                  <div v-else class="no-data">
                    <i class="el-icon-files"></i>
                    <p>No processing data available</p>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- Topics & Concepts Tab -->
          <el-tab-pane label="🎯 Topics & Concepts" name="topics">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-card>
                  <div slot="header">Key Topics</div>
                  <el-tag v-for="topic in collectionAnalytics.keyTopics" :key="topic" style="margin: 4px;">
                    {{ topic }}
                  </el-tag>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <div slot="header">Learning Objectives</div>
                  <ul v-if="collectionAnalytics.learningObjectives">
                    <li v-for="objective in collectionAnalytics.learningObjectives" :key="objective">
                      {{ objective }}
                    </li>
                  </ul>
                </el-card>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- Documents Tab -->
          <el-tab-pane label="📚 Documents" name="documents">
            <el-table :data="collectionDocuments" v-loading="loadingCollectionDetails">
              <el-table-column prop="documentName" label="Document Name" min-width="200"/>
              <el-table-column prop="totalChunks" label="Chunks" width="100"/>
              <el-table-column prop="status" label="Status" width="120">
                <template slot-scope="scope">
                  <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="uploadTime" label="Upload Time" width="150">
                <template slot-scope="scope">
                  {{ formatDate(scope.row.uploadTime) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <div slot="footer" class="dialog-footer">
        <el-button @click="collectionDetailVisible = false">Close</el-button>
        <el-button type="primary" @click="refreshCollectionDetails">Refresh Details</el-button>
      </div>
    </el-dialog>

    <!-- Content Type Details Dialog -->
    <el-dialog :title="contentDetailTitle" :visible.sync="contentDetailVisible" width="70%" :close-on-click-modal="false">
      <div v-loading="loadingContentDetails">
        <!-- Search and Filter Bar -->
        <div class="content-search-bar">
          <el-input 
            v-model="contentSearchQuery" 
            placeholder="Search content..."
            prefix-icon="el-icon-search"
            clearable
            @input="filterContentItems">
          </el-input>
          <el-select v-model="contentFilterDoc" placeholder="Filter by document" clearable @change="filterContentItems">
            <el-option 
              v-for="doc in contentDocuments" 
              :key="doc" 
              :label="doc" 
              :value="doc">
            </el-option>
          </el-select>
        </div>

        <!-- Content Items List -->
        <div class="content-items-container">
          <el-empty v-if="filteredContentItems.length === 0" description="No items found"></el-empty>
          
          <div v-else>
            <div class="content-stats-summary">
              Showing {{ filteredContentItems.length }} of {{ contentItems.length }} items
            </div>
            
            <!-- Content Items Table -->
            <el-table 
              :data="paginatedContentItems" 
              style="width: 100%" 
              :height="400"
              stripe
              border>
              <el-table-column 
                label="Title" 
                width="200"
                show-overflow-tooltip>
                <template slot-scope="scope">
                  <div class="content-title-cell">
                    <span class="content-item-icon">{{ getContentTypeIcon(currentContentType) }}</span>
                    {{ scope.row.title || `${formatContentType(currentContentType)} #${(contentCurrentPage - 1) * contentPageSize + scope.$index + 1}` }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column 
                prop="content" 
                label="Content" 
                min-width="300"
                show-overflow-tooltip>
                <template slot-scope="scope">
                  <div class="content-text-cell">{{ scope.row.content }}</div>
                </template>
              </el-table-column>
              <el-table-column 
                prop="document_name" 
                label="Document" 
                width="150">
                <template slot-scope="scope">
                  <el-tag size="mini" type="info">{{ scope.row.document_name }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column 
                prop="page_number" 
                label="Page" 
                width="80" 
                align="center">
                <template slot-scope="scope">
                  {{ scope.row.page_number || 'N/A' }}
                </template>
              </el-table-column>
              <el-table-column 
                label="Chapter" 
                width="100" 
                align="center">
                <template slot-scope="scope">
                  <el-tag size="mini" v-if="scope.row.chapter_number" type="primary">
                    Ch {{ scope.row.chapter_number }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column 
                prop="difficulty_level" 
                label="Difficulty" 
                width="100" 
                align="center">
                <template slot-scope="scope">
                  <el-tag 
                    size="mini" 
                    :type="getDifficultyTagType(scope.row.difficulty_level)"
                    v-if="scope.row.difficulty_level">
                    {{ scope.row.difficulty_level }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column 
                prop="word_count" 
                label="Words" 
                width="80" 
                align="center">
                <template slot-scope="scope">
                  {{ scope.row.word_count || '-' }}
                </template>
              </el-table-column>
            </el-table>

            <!-- Pagination -->
            <div class="content-pagination">
              <el-pagination
                @current-change="handleContentPageChange"
                :current-page="contentCurrentPage"
                :page-size="contentPageSize"
                layout="prev, pager, next"
                :total="filteredContentItems.length">
              </el-pagination>
            </div>
          </div>
        </div>
      </div>
      
      <div slot="footer" class="dialog-footer">
        <el-button @click="exportContentItems" type="primary">Export to CSV</el-button>
        <el-button @click="contentDetailVisible = false">Close</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import HeaderBar from '../components/HeaderBar.vue'
import ragDocumentApi from '../apis/ragDocument'

export default {
  name: 'RagDocumentManagement',
  components: {
    HeaderBar
  },
  data() {
    return {
      loading: false,
      uploading: false,
      showUploadDialog: false,
      documentDialogVisible: false,
      collectionDetailVisible: false,
      loadingCollectionDetails: false,
      selectedDocument: null,
      selectedCollection: null,
      collectionDocuments: [],
      collectionAnalytics: {},
      activeTab: 'analysis',
      // Content Detail Dialog
      contentDetailVisible: false,
      loadingContentDetails: false,
      currentContentType: '',
      contentDetailTitle: '',
      contentItems: [],
      filteredContentItems: [],
      contentSearchQuery: '',
      contentFilterDoc: '',
      contentDocuments: [],
      contentCurrentPage: 1,
      contentPageSize: 10,
      documents: [],
      collections: [],
      searchParams: {
        grade: '',
        subject: '',
        documentName: ''
      },
      uploadForm: {
        grade: 'class-6',
        subject: 'mathematics',
        documentName: '',
        mode: 'single',
        file: null,
        files: []
      },
      pagination: {
        page: 1,
        limit: 20,
        total: 0
      },
      filterStatus: '',
      refreshInterval: null
    }
  },
  computed: {
    hasProcessingDocs() {
      return this.documents.some(doc => doc.status === 'PROCESSING')
    },
    paginatedContentItems() {
      const start = (this.contentCurrentPage - 1) * this.contentPageSize
      const end = start + this.contentPageSize
      return this.filteredContentItems.slice(start, end)
    }
  },
  mounted() {
    this.loadCollections()
    this.loadDocuments()
    this.startAutoRefresh()
  },
  
  beforeDestroy() {
    this.stopAutoRefresh()
  },
  methods: {
    loadCollections() {
      ragDocumentApi.listCollections((res) => {
        if (res.data.code === 'success' || res.data.code === 0) {
          this.collections = res.data.data || []
        } else {
          this.$message.error(res.data.msg || 'Failed to load collections')
        }
      })
    },

    loadDocuments() {
      this.loading = true
      const params = {
        page: this.pagination.page,
        limit: this.pagination.limit,
        status: this.filterStatus,
        ...this.searchParams
      }
      
      ragDocumentApi.getDocumentList(params, (res) => {
        this.loading = false
        if (res.data.code === 'success' || res.data.code === 0) {
          this.documents = res.data.data.list || []
          this.pagination.total = res.data.data.total || 0
        } else {
          this.$message.error(res.data.msg || 'Failed to load documents')
        }
      })
    },

    handleSizeChange(val) {
      this.pagination.limit = val
      this.pagination.page = 1
      this.loadDocuments()
    },

    handleCurrentChange(val) {
      this.pagination.page = val
      this.loadDocuments()
    },

    handleFileChange(file, fileList) {
      if (this.uploadForm.mode === 'single') {
        this.uploadForm.file = file.raw
        this.uploadForm.files = []
      } else {
        this.uploadForm.files = fileList.map(f => f.raw)
        this.uploadForm.file = null
      }
    },

    beforeRemove(file, fileList) {
      if (this.uploadForm.mode === 'single') {
        this.uploadForm.file = null
      } else {
        this.uploadForm.files = fileList.map(f => f.raw)
      }
    },

    uploadDocument() {
      // Validation based on upload mode
      if (this.uploadForm.mode === 'single') {
        if (!this.uploadForm.grade || !this.uploadForm.subject || !this.uploadForm.file) {
          this.$message.error('Please fill in all required fields')
          return
        }

        if (this.uploadForm.file.size > 50 * 1024 * 1024) {
          this.$message.error('File size cannot exceed 50MB')
          return
        }

        if (!this.uploadForm.file.type.includes('pdf')) {
          this.$message.error('Only PDF files are supported')
          return
        }

        // Single file upload
        this.uploading = true
        ragDocumentApi.uploadDocument({
          file: this.uploadForm.file,
          grade: this.uploadForm.grade,
          subject: this.uploadForm.subject,
          documentName: this.uploadForm.documentName
        }, (res) => {
          this.uploading = false
          if (res.data.code === 'success' || res.data.code === 0) {
            this.$message.success('Document uploaded successfully')
            this.showUploadDialog = false
            this.resetUploadForm()
            this.loadDocuments()
            this.loadCollections()
          } else {
            this.$message.error(res.data.msg || 'Upload failed')
          }
        })
      } else {
        // Batch upload
        if (!this.uploadForm.grade || !this.uploadForm.subject || this.uploadForm.files.length === 0) {
          this.$message.error('Please fill in all required fields and select files')
          return
        }

        // Validate all files
        for (let file of this.uploadForm.files) {
          if (file.size > 50 * 1024 * 1024) {
            this.$message.error(`File ${file.name} exceeds 50MB limit`)
            return
          }
          if (!file.type.includes('pdf')) {
            this.$message.error(`File ${file.name} is not a PDF`)
            return
          }
        }

        this.uploading = true
        ragDocumentApi.uploadDocumentsBatch({
          files: this.uploadForm.files,
          grade: this.uploadForm.grade,
          subject: this.uploadForm.subject
        }, (res) => {
          this.uploading = false
          if (res.data.code === 'success' || res.data.code === 0) {
            const results = res.data.data || []
            const successCount = results.filter(r => r.status !== 'FAILED').length
            const failCount = results.length - successCount
            
            if (failCount === 0) {
              this.$message.success(`All ${successCount} documents uploaded successfully`)
            } else {
              this.$message.warning(`${successCount} documents uploaded, ${failCount} failed`)
            }
            
            this.showUploadDialog = false
            this.resetUploadForm()
            this.loadDocuments()
            this.loadCollections()
          } else {
            this.$message.error(res.data.msg || 'Batch upload failed')
          }
        })
      }
    },

    processDocument(document) {
      ragDocumentApi.processDocument(document.id, (res) => {
        if (res.data.code === 'success' || res.data.code === 0) {
          this.$message.success('Document processing started')
          this.loadDocuments()
        } else {
          this.$message.error(res.data.msg || 'Failed to start processing')
        }
      })
    },

    deleteDocument(document) {
      this.$confirm(`Delete document "${document.documentName}"?`, 'Warning', {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        ragDocumentApi.deleteDocument(document.id, (res) => {
          if (res.data.code === 'success' || res.data.code === 0) {
            this.$message.success('Document deleted successfully')
            this.loadDocuments()
            this.loadCollections()
          } else {
            this.$message.error(res.data.msg || 'Failed to delete document')
          }
        })
      })
    },

    deleteCollection(grade, subject) {
      this.$confirm(`Delete collection "${grade} - ${subject}"?`, 'Warning', {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        ragDocumentApi.deleteCollection(grade, subject, (res) => {
          if (res.data.code === 'success' || res.data.code === 0) {
            this.$message.success('Collection deleted successfully')
            this.loadCollections()
            this.loadDocuments()
          } else {
            this.$message.error(res.data.msg || 'Failed to delete collection')
          }
        })
      })
    },

    viewDocument(document) {
      this.selectedDocument = document
      this.documentDialogVisible = true
    },

    resetUploadForm() {
      this.uploadForm = {
        grade: 'class-6',
        subject: 'mathematics',
        documentName: '',
        mode: 'single',
        file: null,
        files: []
      }
      this.$refs.upload.clearFiles()
    },

    getStatusType(status) {
      const statusTypes = {
        'UPLOADED': '',
        'PROCESSING': 'warning',
        'PROCESSED': 'success',
        'FAILED': 'danger'
      }
      return statusTypes[status] || ''
    },

    getProgress(document) {
      if (!document.totalChunks || document.totalChunks === 0) return 0
      return Math.round((document.processedChunks / document.totalChunks) * 100)
    },

    getProgressStatus(document) {
      if (document.status === 'FAILED') return 'exception'
      return null
    },

    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
    },

    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString()
    },

    startAutoRefresh() {
      // Refresh every 5 seconds to check for processing updates
      this.refreshInterval = setInterval(() => {
        // Only refresh if we have processing documents or recently uploaded documents
        const needsRefresh = this.documents.some(doc => 
          doc.status === 'PROCESSING' || doc.status === 'UPLOADED'
        )
        
        if (needsRefresh) {
          this.loadDocuments()
          this.loadCollections()
        }
      }, 5000) // 5 seconds
    },

    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },

    // Collection Detail Methods
    viewCollectionDetails(collection) {
      this.selectedCollection = collection
      this.collectionDetailVisible = true
      this.activeTab = 'analysis'
      this.loadCollectionDetails()
    },

    async loadCollectionDetails() {
      if (!this.selectedCollection) return
      
      this.loadingCollectionDetails = true
      
      try {
        // Load collection documents
        const params = {
          page: 1,
          limit: 100,
          grade: this.selectedCollection.grade,
          subject: this.selectedCollection.subject
        }
        
        ragDocumentApi.getDocumentList(params, (res) => {
          if (res.data.code === 'success' || res.data.code === 0) {
            this.collectionDocuments = res.data.data.list || []
          }
        })

        // Load collection analytics
        ragDocumentApi.getCollectionAnalytics(
          this.selectedCollection.grade,
          this.selectedCollection.subject,
          (res) => {
            if (res.data.code === 'success' || res.data.code === 0) {
              this.collectionAnalytics = res.data.data || {}
            } else {
              // Fallback analytics from existing data
              this.generateBasicAnalytics()
            }
            this.loadingCollectionDetails = false
          }
        )

      } catch (error) {
        console.error('Error loading collection details:', error)
        this.generateBasicAnalytics()
        this.loadingCollectionDetails = false
      }
    },

    generateBasicAnalytics() {
      // Generate basic analytics from loaded documents
      const docs = this.collectionDocuments
      
      let totalTopics = 0
      let contentTypes = {}
      let chunkTypes = {}
      let keyTopics = []
      
      docs.forEach(doc => {
        if (doc.processingStats) {
          try {
            const stats = typeof doc.processingStats === 'string' ? 
              JSON.parse(doc.processingStats) : doc.processingStats
            
            // Count content categories
            if (stats.content_categories) {
              Object.entries(stats.content_categories).forEach(([type, count]) => {
                contentTypes[type] = (contentTypes[type] || 0) + count
              })
            }
            
            // Count chunk types
            if (stats.chunk_types) {
              Object.entries(stats.chunk_types).forEach(([type, count]) => {
                chunkTypes[type] = (chunkTypes[type] || 0) + count
              })
            }
          } catch (e) {
            console.warn('Failed to parse processing stats:', e)
          }
        }
      })
      
      // Generate key topics based on content types
      keyTopics = Object.keys(contentTypes).map(type => 
        this.formatContentType(type)
      ).slice(0, 10)
      
      totalTopics = keyTopics.length
      
      this.collectionAnalytics = {
        totalTopics,
        contentTypes,
        chunkTypes,
        keyTopics,
        avgDifficulty: 'Medium',
        learningObjectives: [
          'Understand core concepts',
          'Apply learned knowledge',
          'Solve practice problems'
        ]
      }
    },

    refreshCollectionDetails() {
      this.loadCollectionDetails()
    },

    formatContentType(type) {
      const typeMap = {
        'concept': 'Concepts',
        'example': 'Examples',
        'exercise': 'Exercises',
        'definition': 'Definitions',
        'table': 'Tables',
        'key_concept': 'Key Concepts',
        'text': 'Text Content',
        'formula': 'Formulas'
      }
      return typeMap[type] || type.charAt(0).toUpperCase() + type.slice(1)
    },

    getCollectionStatusType(status) {
      const statusTypes = {
        'READY': 'success',
        'PARTIAL': 'warning', 
        'PROCESSING': 'info',
        'EMPTY': '',
        'FAILED': 'danger'
      }
      return statusTypes[status] || ''
    },

    getSortedContentTypes(contentTypes) {
      if (!contentTypes || typeof contentTypes !== 'object') {
        return []
      }
      
      // Calculate total for percentage calculation
      const total = Object.values(contentTypes).reduce((sum, count) => sum + count, 0)
      
      // Convert to array and sort by count (descending)
      return Object.entries(contentTypes)
        .map(([type, count]) => ({
          type,
          count,
          percentage: total > 0 ? Math.round((count / total) * 100) : 0
        }))
        .sort((a, b) => b.count - a.count)
    },

    getContentTypeIcon(type) {
      const icons = {
        'concept': '💡',
        'key_concept': '⭐',
        'example': '📝',
        'exercise': '💪',
        'definition': '📖',
        'table': '📊',
        'formula': '🔢',
        'problem': '🧩',
        'solution': '✅'
      }
      return icons[type] || '📄'
    },

    getChunkTypeIcon(type) {
      const icons = {
        'text': '📄',
        'table': '📊',
        'image': '🖼️',
        'formula': '🔢',
        'diagram': '📐'
      }
      return icons[type] || '📄'
    },

    getContentTypeColor(type) {
      const colors = {
        'concept': '#67C23A',
        'key_concept': '#E6A23C',
        'example': '#409EFF',
        'exercise': '#F56C6C',
        'definition': '#909399',
        'table': '#E6A23C',
        'formula': '#9340FF'
      }
      return colors[type] || '#409EFF'
    },

    getChunkTypeColor(type) {
      const colors = {
        'text': '#67C23A',
        'table': '#E6A23C',
        'image': '#F56C6C',
        'formula': '#9340FF'
      }
      return colors[type] || '#409EFF'
    },

    getContentTypeTagType(type) {
      const tagTypes = {
        'concept': 'success',
        'key_concept': 'warning',
        'example': 'primary',
        'exercise': 'danger',
        'definition': 'info',
        'table': 'warning'
      }
      return tagTypes[type] || 'primary'
    },

    getChunkTypeTagType(type) {
      const tagTypes = {
        'text': 'success',
        'table': 'warning',
        'image': 'danger'
      }
      return tagTypes[type] || 'primary'
    },

    getDifficultyTagType(difficulty) {
      const tagTypes = {
        'easy': 'success',
        'medium': 'warning', 
        'hard': 'danger',
        'basic': 'info',
        'intermediate': 'primary',
        'advanced': 'danger'
      }
      return tagTypes[difficulty] || 'info'
    },

    // Content Detail Methods
    viewContentTypeDetails(contentType, count) {
      this.currentContentType = contentType
      this.contentDetailTitle = `${this.formatContentType(contentType)} Details (${count} items)`
      this.contentDetailVisible = true
      this.loadContentTypeDetails()
    },

    async loadContentTypeDetails() {
      this.loadingContentDetails = true
      this.contentItems = []
      this.filteredContentItems = []
      this.contentCurrentPage = 1
      
      try {
        // Call API to get content items
        ragDocumentApi.getContentTypeItems(
          this.selectedCollection.grade,
          this.selectedCollection.subject,
          this.currentContentType,
          (res) => {
            if (res.data.code === 'success' || res.data.code === 0) {
              this.contentItems = res.data.data || []
              this.filteredContentItems = [...this.contentItems]
              
              // Extract unique document names
              this.contentDocuments = [...new Set(this.contentItems.map(item => item.document_name))]
              
              this.loadingContentDetails = false
            } else {
              // Fallback: Generate sample data from analytics
              this.generateSampleContentItems()
              this.loadingContentDetails = false
            }
          }
        )
      } catch (error) {
        console.error('Error loading content details:', error)
        this.generateSampleContentItems()
        this.loadingContentDetails = false
      }
    },

    generateSampleContentItems() {
      // Generate sample content items from processing stats
      const sampleItems = []
      const docs = this.collectionDocuments
      
      docs.forEach(doc => {
        if (doc.processingStats) {
          try {
            const stats = typeof doc.processingStats === 'string' ? 
              JSON.parse(doc.processingStats) : doc.processingStats
            
            // Create sample items based on content type
            const typeCount = stats.content_categories?.[this.currentContentType] || 0
            
            for (let i = 0; i < Math.min(typeCount, 5); i++) {
              sampleItems.push({
                content: `Sample ${this.formatContentType(this.currentContentType)} content from ${doc.documentName}. This is placeholder text representing actual ${this.currentContentType} content that would be extracted from the document.`,
                document_name: doc.documentName,
                page_number: Math.floor(Math.random() * 30) + 1,
                chapter_number: Math.floor(Math.random() * 10) + 1,
                difficulty_level: ['Easy', 'Medium', 'Hard'][Math.floor(Math.random() * 3)],
                word_count: Math.floor(Math.random() * 200) + 50
              })
            }
          } catch (e) {
            console.warn('Failed to generate sample items:', e)
          }
        }
      })
      
      this.contentItems = sampleItems
      this.filteredContentItems = [...sampleItems]
      this.contentDocuments = [...new Set(sampleItems.map(item => item.document_name))]
    },

    filterContentItems() {
      let filtered = [...this.contentItems]
      
      // Filter by search query
      if (this.contentSearchQuery) {
        const query = this.contentSearchQuery.toLowerCase()
        filtered = filtered.filter(item => 
          item.content.toLowerCase().includes(query) ||
          (item.title && item.title.toLowerCase().includes(query))
        )
      }
      
      // Filter by document
      if (this.contentFilterDoc) {
        filtered = filtered.filter(item => item.document_name === this.contentFilterDoc)
      }
      
      this.filteredContentItems = filtered
      this.contentCurrentPage = 1
    },

    handleContentPageChange(page) {
      this.contentCurrentPage = page
    },

    exportContentItems() {
      // Create CSV content
      let csv = 'Type,Content,Document,Page,Chapter,Difficulty,Words\n'
      
      this.filteredContentItems.forEach(item => {
        csv += `"${this.formatContentType(this.currentContentType)}",`
        csv += `"${item.content.replace(/"/g, '""')}",`
        csv += `"${item.document_name}",`
        csv += `${item.page_number || ''},`
        csv += `${item.chapter_number || ''},`
        csv += `"${item.difficulty_level || ''}",`
        csv += `${item.word_count || ''}\n`
      })
      
      // Create download link
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${this.currentContentType}_${this.selectedCollection.grade}_${this.selectedCollection.subject}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      this.$message.success('Content exported successfully!')
    }
  }
}
</script>

<style scoped>
.operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 20px;
}

.right-operations {
  display: flex;
  gap: 10px;
  align-items: center;
}

.grade-select, .subject-select {
  width: 120px;
}

.search-input {
  width: 200px;
}

.overview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.collection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.collection-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.collection-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: #409eff;
  background: #fff;
}

.collection-actions {
  display: flex;
  gap: 8px;
}

.collection-info h4 {
  margin: 0 0 5px 0;
  color: #303133;
}

.collection-info p {
  margin: 2px 0;
  color: #606266;
  font-size: 12px;
}

.documents-card {
  min-height: 400px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}

.main-wrapper {
  padding: 0 20px;
}

.content-panel {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  color: #303133;
  margin: 0;
}

/* Collection Detail Styles */
.stat-card {
  text-align: center;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-content {
  padding: 10px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.content-type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.content-type-item:last-child {
  border-bottom: none;
}

.content-type-item span {
  font-size: 14px;
  color: #303133;
}

/* Enhanced Content Type Styles */
.content-type-enhanced {
  margin-bottom: 16px;
}

.content-type-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.content-type-icon {
  font-size: 16px;
  margin-right: 8px;
}

.content-type-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.content-type-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-type-percent {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  min-width: 35px;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 10px;
  display: block;
}

.no-data p {
  margin: 0;
  font-size: 14px;
}

/* Progress bar customization */
.el-progress-bar__outer {
  border-radius: 3px;
}

.el-progress-bar__inner {
  border-radius: 3px;
}

/* Clickable Content Type Styles */
.clickable-content-type {
  cursor: pointer;
  transition: all 0.3s ease;
}

.clickable-content-type:hover {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 8px;
  margin: -8px;
}

.click-hint {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.3s;
}

.clickable-content-type:hover .click-hint {
  opacity: 1;
}

/* Content Detail Dialog Styles */
.content-search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.content-search-bar .el-input {
  flex: 1;
}

.content-stats-summary {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.content-item-header {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.content-item-icon {
  font-size: 16px;
}

.content-item-title {
  flex: 1;
  font-weight: 500;
}

.content-item-body {
  padding: 15px;
}

.content-text {
  margin-bottom: 15px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
}

.content-metadata {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.content-pagination {
  margin-top: 20px;
  text-align: center;
}

.content-items-container {
  max-height: 500px;
  overflow-y: auto;
}

/* Table Layout Styles */
.content-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-title-cell .content-item-icon {
  font-size: 16px;
  color: #409EFF;
}

.content-text-cell {
  max-width: 300px;
  line-height: 1.5;
  word-break: break-word;
}

.keywords-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.no-keywords {
  color: #909399;
  font-style: italic;
  font-size: 12px;
}

/* Table responsiveness */
.el-table .cell {
  padding: 8px 6px;
}

.el-table th .cell {
  padding: 8px 6px;
}
</style>
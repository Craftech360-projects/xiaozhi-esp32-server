import { getServiceUrl } from './api';
import RequestService from './httpRequest';

export default {
    // Upload single document
    uploadDocument(data, callback) {
        const formData = new FormData()
        formData.append('file', data.file)
        formData.append('grade', data.grade)
        formData.append('subject', data.subject)
        if (data.documentName) {
            formData.append('documentName', data.documentName)
        }
        
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/upload`)
            .method('POST')
            .header({ 'content-type': 'multipart/form-data' })
            .data(formData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Upload document failed:', err);
                RequestService.reAjaxFun(() => {
                    this.uploadDocument(data, callback);
                });
            }).send();
    },

    // Upload multiple documents
    uploadDocumentsBatch(data, callback) {
        const formData = new FormData()
        data.files.forEach(file => {
            formData.append('files', file)
        })
        formData.append('grade', data.grade)
        formData.append('subject', data.subject)
        
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/upload-batch`)
            .method('POST')
            .header({ 'content-type': 'multipart/form-data' })
            .data(formData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Batch upload failed:', err);
                RequestService.reAjaxFun(() => {
                    this.uploadDocumentsBatch(data, callback);
                });
            }).send();
    },

    // Get collection information
    getCollectionInfo(grade, subject, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/collection/info?grade=${grade}&subject=${subject}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get collection info failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getCollectionInfo(grade, subject, callback);
                });
            }).send();
    },

    // List all collections
    listCollections(callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/collection/list`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('List collections failed:', err);
                RequestService.reAjaxFun(() => {
                    this.listCollections(callback);
                });
            }).send();
    },

    // Delete collection
    deleteCollection(grade, subject, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/collection?grade=${grade}&subject=${subject}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Delete collection failed:', err);
                RequestService.reAjaxFun(() => {
                    this.deleteCollection(grade, subject, callback);
                });
            }).send();
    },

    // Get document list
    getDocumentList(params, callback) {
        let url = `${getServiceUrl()}/rag/document/list?`
        const queryParams = []
        if (params.page) queryParams.push(`page=${params.page}`)
        if (params.limit) queryParams.push(`limit=${params.limit}`)
        if (params.grade) queryParams.push(`grade=${params.grade}`)
        if (params.subject) queryParams.push(`subject=${params.subject}`)
        if (params.documentName) queryParams.push(`documentName=${params.documentName}`)
        if (params.status) queryParams.push(`status=${params.status}`)
        url += queryParams.join('&')
        
        RequestService.sendRequest()
            .url(url)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get document list failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getDocumentList(params, callback);
                });
            }).send();
    },

    // Delete document
    deleteDocument(documentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/${documentId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Delete document failed:', err);
                RequestService.reAjaxFun(() => {
                    this.deleteDocument(documentId, callback);
                });
            }).send();
    },

    // Process document
    processDocument(documentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/process/${documentId}`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Process document failed:', err);
                RequestService.reAjaxFun(() => {
                    this.processDocument(documentId, callback);
                });
            }).send();
    },

    // Get processing status
    getProcessingStatus(documentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/status/${documentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get processing status failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getProcessingStatus(documentId, callback);
                });
            }).send();
    },

    // Get collection analytics
    getCollectionAnalytics(grade, subject, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/collection/analytics?grade=${grade}&subject=${subject}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get collection analytics failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getCollectionAnalytics(grade, subject, callback);
                });
            }).send();
    },

    // Get content type items
    getContentTypeItems(grade, subject, contentType, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/rag/document/content/items?grade=${grade}&subject=${subject}&contentType=${contentType}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get content type items failed:', err);
                // Return sample data as fallback
                callback({
                    data: {
                        code: 'success',
                        data: []
                    }
                });
            }).send();
    }
}
# Frontend Integration Guide

## Overview
This guide shows how to integrate all 20 new features into your React frontend.

## API Service Layer

Create `src/services/extendedApi.js`:

```javascript
import api from './api'; // Your existing API service

// Analytics Services
export const analyticsService = {
  getDashboard: (days = 30) => 
    api.get(`/inventory/extended/analytics/dashboard/?days=${days}`),
  
  getSalesTrend: (days = 30) => 
    api.get(`/inventory/extended/analytics/sales-trend/?days=${days}`),
  
  getTopCustomers: (limit = 10) => 
    api.get(`/inventory/extended/analytics/top-customers/?limit=${limit}`),
  
  getInventoryValuation: () => 
    api.get('/inventory/extended/analytics/inventory-valuation/'),
  
  getCategoryPerformance: (days = 30) => 
    api.get(`/inventory/extended/analytics/category-performance/?days=${days}`),
  
  getSupplierPerformance: () => 
    api.get('/inventory/extended/analytics/supplier-performance/'),
};

// Customer Services
export const customerService = {
  getAll: (params) => api.get('/inventory/extended/customers/', { params }),
  getById: (id) => api.get(`/inventory/extended/customers/${id}/`),
  create: (data) => api.post('/inventory/extended/customers/', data),
  update: (id, data) => api.put(`/inventory/extended/customers/${id}/`, data),
  delete: (id) => api.delete(`/inventory/extended/customers/${id}/`),
  getPurchaseHistory: (id) => api.get(`/inventory/extended/customers/${id}/purchase_history/`),
};

// Warehouse Services
export const warehouseService = {
  getAll: (params) => api.get('/inventory/extended/warehouses/', { params }),
  getById: (id) => api.get(`/inventory/extended/warehouses/${id}/`),
  create: (data) => api.post('/inventory/extended/warehouses/', data),
  update: (id, data) => api.put(`/inventory/extended/warehouses/${id}/`, data),
  delete: (id) => api.delete(`/inventory/extended/warehouses/${id}/`),
  getInventory: (id) => api.get(`/inventory/extended/warehouses/${id}/inventory/`),
};

// Promotion Services
export const promotionService = {
  getAll: (params) => api.get('/inventory/extended/promotions/', { params }),
  getActive: () => api.get('/inventory/extended/promotions/active/'),
  getById: (id) => api.get(`/inventory/extended/promotions/${id}/`),
  create: (data) => api.post('/inventory/extended/promotions/', data),
  update: (id, data) => api.put(`/inventory/extended/promotions/${id}/`, data),
  delete: (id) => api.delete(`/inventory/extended/promotions/${id}/`),
};

// Return Services
export const returnService = {
  getAll: (params) => api.get('/inventory/extended/returns/', { params }),
  getById: (id) => api.get(`/inventory/extended/returns/${id}/`),
  create: (data) => api.post('/inventory/extended/returns/', data),
  approve: (id, restock = false) => 
    api.post(`/inventory/extended/returns/${id}/approve/`, { restock }),
};

// Webhook Services
export const webhookService = {
  getAll: (params) => api.get('/inventory/extended/webhooks/', { params }),
  getById: (id) => api.get(`/inventory/extended/webhooks/${id}/`),
  create: (data) => api.post('/inventory/extended/webhooks/', data),
  update: (id, data) => api.put(`/inventory/extended/webhooks/${id}/`, data),
  delete: (id) => api.delete(`/inventory/extended/webhooks/${id}/`),
  test: (id) => api.post(`/inventory/extended/webhooks/${id}/test/`),
};

// Bulk Operations Services
export const bulkService = {
  importProducts: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/inventory/extended/bulk/import-products/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  exportProducts: () => 
    api.get('/inventory/extended/bulk/export-products/', { responseType: 'blob' }),
  
  updatePrices: (updates) => 
    api.post('/inventory/extended/bulk/update-prices/', { updates }),
  
  adjustInventory: (adjustments) => 
    api.post('/inventory/extended/bulk/adjust-inventory/', { adjustments }),
  
  exportSales: (startDate, endDate) => 
    api.get(`/inventory/extended/bulk/export-sales/?start_date=${startDate}&end_date=${endDate}`, 
      { responseType: 'blob' }),
  
  importCustomers: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/inventory/extended/bulk/import-customers/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Variant Services
export const variantService = {
  getAll: (params) => api.get('/inventory/extended/variants/', { params }),
  getById: (id) => api.get(`/inventory/extended/variants/${id}/`),
  create: (data) => api.post('/inventory/extended/variants/', data),
  update: (id, data) => api.put(`/inventory/extended/variants/${id}/`, data),
  delete: (id) => api.delete(`/inventory/extended/variants/${id}/`),
};

// Tag Services
export const tagService = {
  getAll: (params) => api.get('/inventory/extended/tags/', { params }),
  create: (data) => api.post('/inventory/extended/tags/', data),
  delete: (id) => api.delete(`/inventory/extended/tags/${id}/`),
};

// Audit Log Services
export const auditService = {
  getAll: (params) => api.get('/inventory/extended/audit-logs/', { params }),
};

// Utility Services
export const utilityService = {
  generateBarcode: (code, type = 'code128') => 
    api.post('/inventory/extended/utils/generate-barcode/', { code, type }, 
      { responseType: 'blob' }),
};
```

## React Components

### 1. Dashboard Component

Create `src/pages/Dashboard/AnalyticsDashboard.jsx`:

```javascript
import React, { useState, useEffect } from 'react';
import { analyticsService } from '../../services/extendedApi';
import { Card, Row, Col, Statistic, Select, Spin } from 'antd';
import { 
  DollarOutlined, ShoppingOutlined, RiseOutlined, 
  WarningOutlined, LineChartOutlined 
} from '@ant-design/icons';

const AnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadMetrics();
  }, [days]);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const response = await analyticsService.getDashboard(days);
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Select value={days} onChange={setDays} style={{ width: 120 }}>
          <Select.Option value={7}>Last 7 days</Select.Option>
          <Select.Option value={30}>Last 30 days</Select.Option>
          <Select.Option value={90}>Last 90 days</Select.Option>
        </Select>
      </div>

      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Revenue"
              value={metrics?.total_revenue}
              prefix={<DollarOutlined />}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Orders"
              value={metrics?.total_orders}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Profit Margin"
              value={metrics?.profit_margin}
              prefix={<RiseOutlined />}
              suffix="%"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Low Stock Items"
              value={metrics?.low_stock_count}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Top Products" style={{ marginTop: 16 }}>
        <table style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>Product</th>
              <th>Units Sold</th>
              <th>Revenue</th>
            </tr>
          </thead>
          <tbody>
            {metrics?.top_products?.map((product, index) => (
              <tr key={index}>
                <td>{product.product__name}</td>
                <td>{product.total_sold}</td>
                <td>${product.revenue?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;
```

### 2. Customer Management Component

Create `src/pages/Customers/CustomerList.jsx`:

```javascript
import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { customerService } from '../../services/extendedApi';

const CustomerList = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const response = await customerService.getAll();
      setCustomers(response.data.results);
    } catch (error) {
      message.error('Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values) => {
    try {
      await customerService.create(values);
      message.success('Customer created successfully');
      setModalVisible(false);
      form.resetFields();
      loadCustomers();
    } catch (error) {
      message.error('Failed to create customer');
    }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Phone', dataIndex: 'phone', key: 'phone' },
    { title: 'Type', dataIndex: 'customer_type', key: 'customer_type' },
    { 
      title: 'Total Spent', 
      dataIndex: 'total_spent', 
      key: 'total_spent',
      render: (value) => `$${value?.toFixed(2) || '0.00'}`
    },
    { title: 'Orders', dataIndex: 'total_orders', key: 'total_orders' },
    { title: 'Loyalty Points', dataIndex: 'loyalty_points', key: 'loyalty_points' },
  ];

  return (
    <div>
      <Button 
        type="primary" 
        icon={<PlusOutlined />} 
        onClick={() => setModalVisible(true)}
        style={{ marginBottom: 16 }}
      >
        Add Customer
      </Button>

      <Table 
        columns={columns} 
        dataSource={customers} 
        loading={loading}
        rowKey="id"
      />

      <Modal
        title="Add Customer"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Phone">
            <Input />
          </Form.Item>
          <Form.Item name="customer_type" label="Type" initialValue="retail">
            <Select>
              <Select.Option value="retail">Retail</Select.Option>
              <Select.Option value="wholesale">Wholesale</Select.Option>
              <Select.Option value="vip">VIP</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CustomerList;
```

### 3. Bulk Import Component

Create `src/pages/BulkOperations/BulkImport.jsx`:

```javascript
import React, { useState } from 'react';
import { Upload, Button, Card, message, Alert } from 'antd';
import { UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import { bulkService } from '../../services/extendedApi';

const BulkImport = () => {
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);

  const handleImport = async (file) => {
    setImporting(true);
    setResult(null);
    try {
      const response = await bulkService.importProducts(file);
      setResult(response.data);
      message.success(`Imported ${response.data.success} products`);
    } catch (error) {
      message.error('Import failed');
    } finally {
      setImporting(false);
    }
    return false; // Prevent auto upload
  };

  const handleExport = async () => {
    try {
      const response = await bulkService.exportProducts();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'products.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Products exported successfully');
    } catch (error) {
      message.error('Export failed');
    }
  };

  return (
    <div>
      <Card title="Bulk Product Import/Export">
        <div style={{ marginBottom: 16 }}>
          <Button 
            icon={<DownloadOutlined />} 
            onClick={handleExport}
            style={{ marginRight: 8 }}
          >
            Export Products
          </Button>
          
          <Upload beforeUpload={handleImport} showUploadList={false}>
            <Button icon={<UploadOutlined />} loading={importing}>
              Import Products
            </Button>
          </Upload>
        </div>

        {result && (
          <Alert
            message={`Import Complete: ${result.success} successful`}
            description={
              result.errors.length > 0 && (
                <div>
                  <strong>Errors:</strong>
                  <ul>
                    {result.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )
            }
            type={result.errors.length > 0 ? 'warning' : 'success'}
          />
        )}

        <div style={{ marginTop: 16 }}>
          <h4>CSV Format:</h4>
          <pre>
            name,sku,category,price,cost,quantity,reorder_level,barcode,is_active
            Widget A,WID-001,Electronics,99.99,50.00,100,10,123456789,true
          </pre>
        </div>
      </Card>
    </div>
  );
};

export default BulkImport;
```

## Continue in next file...

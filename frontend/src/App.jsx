import { useEffect, useMemo, useState } from "react";

const API_V1 = "/api/v1";

const money = (value) =>
  Number(value || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

const formatApiError = (detail) => {
  if (!detail) return "Something went wrong. Konjam check pannunga.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const where = Array.isArray(item?.loc) ? item.loc.join(" -> ") : "field";
        return `${where}: ${item?.msg || "invalid value"}`;
      })
      .join(" | ");
  }
  if (typeof detail === "object") {
    if (detail.msg) return detail.msg;
    return JSON.stringify(detail);
  }
  return String(detail);
};

const decodeJwt = (token) => {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

async function api(path, token, options = {}) {
  const response = await fetch(`${API_V1}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }
  if (response.status === 401) {
    localStorage.removeItem("schoolpos_token");
    window.location.href = "/";
    throw new Error("Session expired. Please login again.");
  }
  if (!response.ok) {
    throw new Error(formatApiError(data?.detail));
  }
  return data;
}

function StatCard({ title, value, hint }) {
  return (
    <div className="card stat">
      <p className="muted">{title}</p>
      <h3>{value}</h3>
      <small>{hint}</small>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("schoolpos_token") || "");
  const [role, setRole] = useState("Guest");
  const [tab, setTab] = useState("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [events, setEvents] = useState([]);

  const [salesSummary, setSalesSummary] = useState({ invoices: 0, sales_total: 0, tax_total: 0 });
  const [feeSummary, setFeeSummary] = useState({ receipts: 0, fee_total: 0 });
  const [lowStock, setLowStock] = useState([]);
  const [mostSold, setMostSold] = useState([]);

  const [students, setStudents] = useState([]);
  const [studentMeta, setStudentMeta] = useState({ total: 0, limit: 50, offset: 0 });
  const [studentFilter, setStudentFilter] = useState({ q: "", class_name: "", section: "" });
  const [studentForm, setStudentForm] = useState({
    id: "",
    student_code: "",
    first_name: "",
    last_name: "",
    date_of_birth: "",
    class_name: "",
    section: "",
    is_active: true,
    parent_name: "",
    parent_relation: "Father",
    parent_phone: "",
  });
  const [feeForm, setFeeForm] = useState({
    student_id: "",
    receipt_no: "",
    period: "",
    amount: "",
    payment_mode: "cash",
  });

  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [supplierForm, setSupplierForm] = useState({ name: "", phone: "", email: "", address: "" });
  const [productForm, setProductForm] = useState({
    id: "",
    sku: "",
    barcode: "",
    name: "",
    category: "books",
    supplier_id: "",
    cost_price: "",
    selling_price: "",
    is_tax_inclusive: false,
    tax_profile_id: "",
    stock_on_hand: 0,
    reorder_level: 5,
    is_active: true,
  });
  const [stockMoveForm, setStockMoveForm] = useState({
    product_id: "",
    movement_type: "in",
    quantity: "",
    reason: "",
  });

  const [taxProfiles, setTaxProfiles] = useState([]);
  const [taxForm, setTaxForm] = useState({ id: "", name: "", cgst_rate: 0, sgst_rate: 0, is_active: true });

  const [invoiceItems, setInvoiceItems] = useState([]);
  const [invoiceStudentId, setInvoiceStudentId] = useState("");
  const [discountType, setDiscountType] = useState("");
  const [discountValue, setDiscountValue] = useState("");
  const [paymentMode, setPaymentMode] = useState("cash");
  const [paymentReference, setPaymentReference] = useState("");
  const [invoiceResult, setInvoiceResult] = useState(null);

  const [reportRange, setReportRange] = useState({ start: "", end: "" });
  const [peakHours, setPeakHours] = useState([]);

  const roleFromToken = useMemo(() => decodeJwt(token)?.role || "Guest", [token]);

  useEffect(() => {
    setRole(roleFromToken);
  }, [roleFromToken]);

  const can = (allowedRoles) => allowedRoles.includes(role);

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(""), 2500);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const form = new FormData(e.currentTarget);
      const payload = {
        username: form.get("username"),
        password: form.get("password"),
      };
      const data = await fetch(`${API_V1}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(async (res) => {
        const body = await res.json();
        if (!res.ok) {
          throw new Error(body.detail || "Login failed");
        }
        return body;
      });
      localStorage.setItem("schoolpos_token", data.access_token);
      setToken(data.access_token);
      showToast("Login success! Epdi iruka, dashboard ready.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("schoolpos_token");
    setToken("");
    setRole("Guest");
    setTab("dashboard");
  };

  const loadDashboard = async () => {
    if (!token) return;
    const rangeQuery =
      reportRange.start && reportRange.end ? `?start=${reportRange.start}&end=${reportRange.end}` : "";
    try {
      if (can(["Admin", "Accountant"])) {
        const sales = await api(`/reports/sales/summary${rangeQuery}`, token);
        const fees = await api(`/reports/fees/summary${rangeQuery}`, token);
        const sold = await api(`/reports/analytics/most-sold${rangeQuery ? `${rangeQuery}&limit=6` : "?limit=6"}`, token);
        setSalesSummary(sales);
        setFeeSummary(fees);
        setMostSold(sold);
      }
      if (can(["Admin", "Staff"])) {
        const stock = await api("/reports/inventory/low-stock?limit=10", token);
        setLowStock(stock);
      }
      if (can(["Admin", "Accountant"])) {
        const peak = await api("/reports/analytics/peak-hours?days=30", token);
        setPeakHours(peak);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const loadStudents = async () => {
    if (!token || !can(["Admin", "Staff", "Accountant"])) return;
    const params = new URLSearchParams({ limit: "50", offset: String(studentMeta.offset || 0) });
    if (studentFilter.q) params.set("q", studentFilter.q);
    if (studentFilter.class_name) params.set("class_name", studentFilter.class_name);
    if (studentFilter.section) params.set("section", studentFilter.section);
    const data = await api(`/students?${params.toString()}`, token);
    setStudents(data.items || []);
    setStudentMeta(data.meta || { total: 0, limit: 50, offset: 0 });
  };

  const loadSuppliersProductsTax = async () => {
    if (!token) return;
    if (can(["Admin", "Staff", "Accountant"])) {
      const productsData = await api("/inventory/products?limit=200&offset=0", token);
      setProducts(productsData.items || []);
      const taxData = await api("/tax/profiles?limit=200&offset=0", token);
      setTaxProfiles(taxData.items || []);
    }
    if (can(["Admin", "Staff"])) {
      const suppliersData = await api("/inventory/suppliers?limit=200&offset=0", token);
      setSuppliers(suppliersData.items || []);
    }
  };

  useEffect(() => {
    if (!token) return;
    setError("");
    loadDashboard();
    loadStudents().catch((err) => setError(err.message));
    loadSuppliersProductsTax().catch((err) => setError(err.message));
  }, [token, role]);

  useEffect(() => {
    if (!token) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${wsScheme}://${window.location.host}/ws`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents((prev) => [data, ...prev.slice(0, 14)]);
        if (data.event === "stock.updated" || data.event === "sale.created") {
          loadDashboard();
          loadSuppliersProductsTax().catch(() => null);
        }
      } catch {
        // Ignore malformed events.
      }
    };
    return () => ws.close();
  }, [token]);

  const saveStudent = async (e) => {
    e.preventDefault();
    if (!can(["Admin", "Staff"])) {
      setError("You cannot save student data.");
      return;
    }
    if ((studentForm.student_code || "").trim().length < 2) {
      setError("Student Code minimum 2 characters venum.");
      return;
    }
    if (!(studentForm.class_name || "").trim()) {
      setError("Class Name mandatory da.");
      return;
    }
    if (!(studentForm.first_name || "").trim()) {
      setError("First Name mandatory da.");
      return;
    }
    const payload = {
      student_code: studentForm.student_code,
      first_name: studentForm.first_name,
      last_name: studentForm.last_name || null,
      date_of_birth: studentForm.date_of_birth || null,
      class_name: studentForm.class_name,
      section: studentForm.section || null,
      is_active: studentForm.is_active,
      parents: studentForm.parent_name
        ? [
            {
              relation: studentForm.parent_relation,
              name: studentForm.parent_name,
              phone: studentForm.parent_phone || null,
            },
          ]
        : [],
    };
    try {
      if (studentForm.id) {
        await api(`/students/${studentForm.id}`, token, { method: "PUT", body: JSON.stringify(payload) });
        showToast("Student update aachu da!");
      } else {
        await api("/students", token, { method: "POST", body: JSON.stringify(payload) });
        showToast("Student create super-a mudinjudhu.");
      }
      setStudentForm({
        id: "",
        student_code: "",
        first_name: "",
        last_name: "",
        date_of_birth: "",
        class_name: "",
        section: "",
        is_active: true,
        parent_name: "",
        parent_relation: "Father",
        parent_phone: "",
      });
      await loadStudents();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeStudent = async (id) => {
    try {
      await api(`/students/${id}`, token, { method: "DELETE" });
      showToast("Student delete pannitom.");
      await loadStudents();
    } catch (err) {
      setError(err.message);
    }
  };

  const addFee = async (e) => {
    e.preventDefault();
    try {
      await api(`/students/${feeForm.student_id}/fees`, token, {
        method: "POST",
        body: JSON.stringify({
          receipt_no: feeForm.receipt_no,
          period: feeForm.period,
          amount: Number(feeForm.amount),
          payment_mode: feeForm.payment_mode,
        }),
      });
      setFeeForm({ student_id: "", receipt_no: "", period: "", amount: "", payment_mode: "cash" });
      showToast("Fees receipt entry done. Semma clean!");
      loadDashboard();
    } catch (err) {
      setError(err.message);
    }
  };

  const addSupplier = async (e) => {
    e.preventDefault();
    try {
      await api("/inventory/suppliers", token, { method: "POST", body: JSON.stringify(supplierForm) });
      setSupplierForm({ name: "", phone: "", email: "", address: "" });
      await loadSuppliersProductsTax();
      showToast("Supplier add pannitom.");
    } catch (err) {
      setError(err.message);
    }
  };

  const saveProduct = async (e) => {
    e.preventDefault();
    const payload = {
      sku: productForm.sku,
      barcode: productForm.barcode || null,
      name: productForm.name,
      category: productForm.category,
      supplier_id: productForm.supplier_id || null,
      cost_price: Number(productForm.cost_price),
      selling_price: Number(productForm.selling_price),
      is_tax_inclusive: productForm.is_tax_inclusive,
      tax_profile_id: productForm.tax_profile_id || null,
      stock_on_hand: Number(productForm.stock_on_hand),
      reorder_level: Number(productForm.reorder_level),
      is_active: productForm.is_active,
    };
    try {
      if (productForm.id) {
        await api(`/inventory/products/${productForm.id}`, token, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await api("/inventory/products", token, { method: "POST", body: JSON.stringify(payload) });
      }
      setProductForm({
        id: "",
        sku: "",
        barcode: "",
        name: "",
        category: "books",
        supplier_id: "",
        cost_price: "",
        selling_price: "",
        is_tax_inclusive: false,
        tax_profile_id: "",
        stock_on_hand: 0,
        reorder_level: 5,
        is_active: true,
      });
      await loadSuppliersProductsTax();
      showToast("Product save complete boss.");
    } catch (err) {
      setError(err.message);
    }
  };

  const moveStock = async (e) => {
    e.preventDefault();
    try {
      await api("/inventory/stock/move", token, {
        method: "POST",
        body: JSON.stringify({
          product_id: stockMoveForm.product_id,
          movement_type: stockMoveForm.movement_type,
          quantity: Number(stockMoveForm.quantity),
          reason: stockMoveForm.reason || null,
        }),
      });
      setStockMoveForm({ product_id: "", movement_type: "in", quantity: "", reason: "" });
      await loadSuppliersProductsTax();
      showToast("Stock movement done. Live update vandhuduchu.");
    } catch (err) {
      setError(err.message);
    }
  };

  const saveTax = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: taxForm.name,
        cgst_rate: Number(taxForm.cgst_rate),
        sgst_rate: Number(taxForm.sgst_rate),
        is_active: taxForm.is_active,
      };
      if (taxForm.id) {
        await api(`/tax/profiles/${taxForm.id}`, token, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await api("/tax/profiles", token, { method: "POST", body: JSON.stringify(payload) });
      }
      setTaxForm({ id: "", name: "", cgst_rate: 0, sgst_rate: 0, is_active: true });
      await loadSuppliersProductsTax();
      showToast("Tax profile set aagiduchu.");
    } catch (err) {
      setError(err.message);
    }
  };

  const invoicePreview = useMemo(() => {
    let subtotal = 0;
    let tax = 0;
    invoiceItems.forEach((row) => {
      const product = products.find((p) => p.id === row.product_id);
      if (!product) return;
      const qty = Number(row.quantity || 0);
      const lineInput = Number(product.selling_price || 0) * qty;
      const tp = taxProfiles.find((t) => t.id === product.tax_profile_id);
      const rate = tp ? Number(tp.cgst_rate) + Number(tp.sgst_rate) : 0;
      if (product.is_tax_inclusive && rate > 0) {
        const lineBase = lineInput / (1 + rate / 100);
        const lineTax = lineInput - lineBase;
        subtotal += Number(lineBase.toFixed(2));
        tax += Number(lineTax.toFixed(2));
      } else {
        const lineBase = lineInput;
        const lineTax = (lineBase * rate) / 100;
        subtotal += Number(lineBase.toFixed(2));
        tax += Number(lineTax.toFixed(2));
      }
    });
    subtotal = Number(subtotal.toFixed(2));
    tax = Number(tax.toFixed(2));
    const discountRaw = Number(discountValue || 0);
    const discountAmount =
      discountType === "percent" ? (subtotal * discountRaw) / 100 : discountType === "flat" ? discountRaw : 0;
    const grandTotal = Number(Math.max(0, subtotal - discountAmount + tax).toFixed(2));
    return { subtotal, tax, discountAmount, grandTotal };
  }, [invoiceItems, products, taxProfiles, discountType, discountValue]);

  const createInvoice = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        student_id: invoiceStudentId || null,
        items: invoiceItems.map((row) => ({
          product_id: row.product_id,
          quantity: Number(row.quantity),
        })),
        discount_type: discountType || null,
        discount_value: Number(discountValue || 0),
        payments: [
          {
            mode: paymentMode,
            amount: Number(invoicePreview.grandTotal.toFixed(2)),
            reference: paymentReference || null,
          },
        ],
      };
      const result = await api("/pos/invoices", token, { method: "POST", body: JSON.stringify(payload) });
      setInvoiceResult(result);
      setInvoiceItems([]);
      setInvoiceStudentId("");
      setDiscountType("");
      setDiscountValue("");
      setPaymentReference("");
      showToast("Invoice create pannitom. Bill ready!");
      loadDashboard();
      loadSuppliersProductsTax();
    } catch (err) {
      setError(err.message);
    }
  };

  const addInvoiceItemRow = () => {
    setInvoiceItems((prev) => [...prev, { product_id: "", quantity: 1 }]);
  };

  if (!token) {
    return (
      <div className="login-wrap">
        <form className="login-card" onSubmit={handleLogin}>
          <h2>School POS - Vanakkam!</h2>
          <p className="muted">Epdi iruka? Login panni ulle vaanga.</p>
          <label>
            Username
            <input name="username" defaultValue="admin" required />
          </label>
          <label>
            Password
            <input name="password" type="password" defaultValue="Admin@123" required />
          </label>
          {error && <div className="error">{error}</div>}
          <button disabled={loading} type="submit">
            {loading ? "Login pannitu irukom..." : "Login"}
          </button>
          <small className="muted">Default: admin / Admin@123</small>
        </form>
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Idhu Home Page da!</h2>
        <p className="muted">Role: {role}</p>
        <nav>
          {["dashboard", "students", "inventory", "tax", "pos", "reports"].map((t) => (
            <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
              {t.toUpperCase()}
            </button>
          ))}
        </nav>
        <button className="ghost" onClick={logout}>
          Logout
        </button>
      </aside>

      <main className="content">
        <header className="topbar">
          <h1>School POS Dashboard - Nalla clean UI</h1>
          <div className="row">
            <input
              type="date"
              value={reportRange.start}
              onChange={(e) => setReportRange((prev) => ({ ...prev, start: e.target.value }))}
            />
            <input
              type="date"
              value={reportRange.end}
              onChange={(e) => setReportRange((prev) => ({ ...prev, end: e.target.value }))}
            />
            <button onClick={loadDashboard}>Refresh Dashboard</button>
          </div>
        </header>

        {error && <div className="error">{error}</div>}
        {toast && <div className="toast">{toast}</div>}

        {tab === "dashboard" && (
          <section>
            <div className="grid4">
              <StatCard title="Sales Total" value={`Rs ${money(salesSummary.sales_total)}`} hint="Inga total sales iruku" />
              <StatCard title="Invoices" value={salesSummary.invoices} hint="Bill count" />
              <StatCard title="Fee Total" value={`Rs ${money(feeSummary.fee_total)}`} hint="Fees collection" />
              <StatCard title="Tax Total" value={`Rs ${money(salesSummary.tax_total)}`} hint="CGST + SGST total" />
            </div>
            <div className="grid2">
              <div className="card">
                <h3>Low Stock - Konjam paathu refill pannunga</h3>
                <table>
                  <thead>
                    <tr><th>SKU</th><th>Name</th><th>Stock</th><th>Reorder</th></tr>
                  </thead>
                  <tbody>
                    {lowStock.map((r) => (
                      <tr key={r.id}><td>{r.sku}</td><td>{r.name}</td><td>{r.stock_on_hand}</td><td>{r.reorder_level}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="card">
                <h3>Most Sold - Semma moving items</h3>
                <table>
                  <thead>
                    <tr><th>SKU</th><th>Name</th><th>Qty</th></tr>
                  </thead>
                  <tbody>
                    {mostSold.map((r) => (
                      <tr key={r.sku}><td>{r.sku}</td><td>{r.name}</td><td>{r.quantity}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="grid2">
              <div className="card">
                <h3>Peak Hours</h3>
                <div className="bars">
                  {peakHours.map((p) => (
                    <div key={p.hour} className="bar-row">
                      <span>{String(p.hour).padStart(2, "0")}:00</span>
                      <div className="bar" style={{ width: `${Math.min(100, p.count * 10)}%` }}>{p.count}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <h3>Live Events - WS</h3>
                <ul className="events">
                  {events.map((ev, i) => (
                    <li key={`${ev.event}-${i}`}>
                      <strong>{ev.event}</strong> - {JSON.stringify(ev.payload)}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        )}

        {tab === "students" && (
          <section className="grid2">
            <div className="card">
              <h3>Student Form - Pudhu / Edit</h3>
              <form onSubmit={saveStudent} className="form-grid">
                <input placeholder="Student Code (min 2 chars)" minLength={2} value={studentForm.student_code} onChange={(e) => setStudentForm({ ...studentForm, student_code: e.target.value })} required />
                <input placeholder="First Name" value={studentForm.first_name} onChange={(e) => setStudentForm({ ...studentForm, first_name: e.target.value })} required />
                <input placeholder="Last Name" value={studentForm.last_name} onChange={(e) => setStudentForm({ ...studentForm, last_name: e.target.value })} />
                <input type="date" value={studentForm.date_of_birth} onChange={(e) => setStudentForm({ ...studentForm, date_of_birth: e.target.value })} />
                <input placeholder="Class Name" value={studentForm.class_name} onChange={(e) => setStudentForm({ ...studentForm, class_name: e.target.value })} required />
                <input placeholder="Section" value={studentForm.section} onChange={(e) => setStudentForm({ ...studentForm, section: e.target.value })} />
                <input placeholder="Parent Name" value={studentForm.parent_name} onChange={(e) => setStudentForm({ ...studentForm, parent_name: e.target.value })} />
                <input placeholder="Parent Phone" value={studentForm.parent_phone} onChange={(e) => setStudentForm({ ...studentForm, parent_phone: e.target.value })} />
                <select value={studentForm.parent_relation} onChange={(e) => setStudentForm({ ...studentForm, parent_relation: e.target.value })}>
                  <option>Father</option><option>Mother</option><option>Guardian</option>
                </select>
                <label className="check"><input type="checkbox" checked={studentForm.is_active} onChange={(e) => setStudentForm({ ...studentForm, is_active: e.target.checked })} /> Active</label>
                <button type="submit">{studentForm.id ? "Update Student" : "Create Student"}</button>
              </form>
              <hr />
              <h4>Add Fee Receipt</h4>
              <form onSubmit={addFee} className="form-grid">
                <select value={feeForm.student_id} onChange={(e) => setFeeForm({ ...feeForm, student_id: e.target.value })} required>
                  <option value="">Select Student</option>
                  {students.map((s) => <option key={s.id} value={s.id}>{s.student_code} - {s.first_name}</option>)}
                </select>
                <input placeholder="Receipt No" value={feeForm.receipt_no} onChange={(e) => setFeeForm({ ...feeForm, receipt_no: e.target.value })} required />
                <input placeholder="Period (2026-Q1)" value={feeForm.period} onChange={(e) => setFeeForm({ ...feeForm, period: e.target.value })} required />
                <input type="number" step="0.01" placeholder="Amount" value={feeForm.amount} onChange={(e) => setFeeForm({ ...feeForm, amount: e.target.value })} required />
                <input placeholder="Mode" value={feeForm.payment_mode} onChange={(e) => setFeeForm({ ...feeForm, payment_mode: e.target.value })} required />
                <button type="submit">Save Fee</button>
              </form>
            </div>

            <div className="card">
              <h3>Students List</h3>
              <div className="row">
                <input placeholder="Search q" value={studentFilter.q} onChange={(e) => setStudentFilter({ ...studentFilter, q: e.target.value })} />
                <input placeholder="Class" value={studentFilter.class_name} onChange={(e) => setStudentFilter({ ...studentFilter, class_name: e.target.value })} />
                <input placeholder="Section" value={studentFilter.section} onChange={(e) => setStudentFilter({ ...studentFilter, section: e.target.value })} />
                <button onClick={() => loadStudents().catch((err) => setError(err.message))}>Search</button>
              </div>
              <p className="muted">Total: {studentMeta.total}</p>
              <table>
                <thead><tr><th>Code</th><th>Name</th><th>Class</th><th>Section</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td>{s.student_code}</td>
                      <td>{s.first_name} {s.last_name}</td>
                      <td>{s.class_name}</td>
                      <td>{s.section}</td>
                      <td>{s.is_active ? "Active" : "Inactive"}</td>
                      <td className="row">
                        <button onClick={() => setStudentForm({
                          id: s.id,
                          student_code: s.student_code,
                          first_name: s.first_name,
                          last_name: s.last_name || "",
                          date_of_birth: s.date_of_birth || "",
                          class_name: s.class_name,
                          section: s.section || "",
                          is_active: s.is_active,
                          parent_name: s.parents?.[0]?.name || "",
                          parent_relation: s.parents?.[0]?.relation || "Father",
                          parent_phone: s.parents?.[0]?.phone || "",
                        })}>Edit</button>
                        {can(["Admin"]) && <button className="danger" onClick={() => removeStudent(s.id)}>Delete</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "inventory" && (
          <section className="grid2">
            <div className="card">
              <h3>Suppliers + Products</h3>
              {can(["Admin"]) && (
                <form onSubmit={addSupplier} className="form-grid">
                  <input placeholder="Supplier Name" value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} required />
                  <input placeholder="Phone" value={supplierForm.phone} onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })} />
                  <input placeholder="Email" value={supplierForm.email} onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })} />
                  <input placeholder="Address" value={supplierForm.address} onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })} />
                  <button type="submit">Add Supplier</button>
                </form>
              )}
              <hr />
              <form onSubmit={saveProduct} className="form-grid">
                <input placeholder="SKU" value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} required />
                <input placeholder="Barcode" value={productForm.barcode} onChange={(e) => setProductForm({ ...productForm, barcode: e.target.value })} />
                <input placeholder="Name" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} required />
                <input placeholder="Category" value={productForm.category} onChange={(e) => setProductForm({ ...productForm, category: e.target.value })} required />
                <select value={productForm.supplier_id} onChange={(e) => setProductForm({ ...productForm, supplier_id: e.target.value })}>
                  <option value="">No Supplier</option>
                  {suppliers.map((s) => <option value={s.id} key={s.id}>{s.name}</option>)}
                </select>
                <select value={productForm.tax_profile_id} onChange={(e) => setProductForm({ ...productForm, tax_profile_id: e.target.value })}>
                  <option value="">No Tax Profile</option>
                  {taxProfiles.map((t) => <option value={t.id} key={t.id}>{t.name}</option>)}
                </select>
                <input type="number" step="0.01" placeholder="Cost Price" value={productForm.cost_price} onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })} required />
                <input type="number" step="0.01" placeholder="Selling Price" value={productForm.selling_price} onChange={(e) => setProductForm({ ...productForm, selling_price: e.target.value })} required />
                <input type="number" placeholder="Stock On Hand" value={productForm.stock_on_hand} onChange={(e) => setProductForm({ ...productForm, stock_on_hand: e.target.value })} required />
                <input type="number" placeholder="Reorder Level" value={productForm.reorder_level} onChange={(e) => setProductForm({ ...productForm, reorder_level: e.target.value })} required />
                <label className="check"><input type="checkbox" checked={productForm.is_tax_inclusive} onChange={(e) => setProductForm({ ...productForm, is_tax_inclusive: e.target.checked })} /> Tax Inclusive</label>
                <label className="check"><input type="checkbox" checked={productForm.is_active} onChange={(e) => setProductForm({ ...productForm, is_active: e.target.checked })} /> Active</label>
                <button type="submit">{productForm.id ? "Update Product" : "Create Product"}</button>
              </form>
              <hr />
              <h4>Stock Move</h4>
              <form onSubmit={moveStock} className="form-grid">
                <select value={stockMoveForm.product_id} onChange={(e) => setStockMoveForm({ ...stockMoveForm, product_id: e.target.value })} required>
                  <option value="">Product</option>
                  {products.map((p) => <option key={p.id} value={p.id}>{p.sku} - {p.name}</option>)}
                </select>
                <select value={stockMoveForm.movement_type} onChange={(e) => setStockMoveForm({ ...stockMoveForm, movement_type: e.target.value })}>
                  <option value="in">in</option><option value="out">out</option><option value="adjust">adjust</option>
                </select>
                <input type="number" placeholder="Quantity" value={stockMoveForm.quantity} onChange={(e) => setStockMoveForm({ ...stockMoveForm, quantity: e.target.value })} required />
                <input placeholder="Reason" value={stockMoveForm.reason} onChange={(e) => setStockMoveForm({ ...stockMoveForm, reason: e.target.value })} />
                <button type="submit">Move Stock</button>
              </form>
            </div>
            <div className="card">
              <h3>Products List</h3>
              <table>
                <thead><tr><th>SKU</th><th>Name</th><th>Category</th><th>Stock</th><th>Price</th><th>Action</th></tr></thead>
                <tbody>
                  {products.map((p) => (
                    <tr key={p.id}>
                      <td>{p.sku}</td><td>{p.name}</td><td>{p.category}</td><td>{p.stock_on_hand}</td><td>{money(p.selling_price)}</td>
                      <td><button onClick={() => setProductForm({ ...p })}>Edit</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "tax" && (
          <section className="grid2">
            <div className="card">
              <h3>Tax Profile Setup</h3>
              <form onSubmit={saveTax} className="form-grid">
                <input placeholder="Tax Name" value={taxForm.name} onChange={(e) => setTaxForm({ ...taxForm, name: e.target.value })} required />
                <input type="number" step="0.01" placeholder="CGST %" value={taxForm.cgst_rate} onChange={(e) => setTaxForm({ ...taxForm, cgst_rate: e.target.value })} required />
                <input type="number" step="0.01" placeholder="SGST %" value={taxForm.sgst_rate} onChange={(e) => setTaxForm({ ...taxForm, sgst_rate: e.target.value })} required />
                <label className="check"><input type="checkbox" checked={taxForm.is_active} onChange={(e) => setTaxForm({ ...taxForm, is_active: e.target.checked })} /> Active</label>
                <button type="submit">{taxForm.id ? "Update Tax" : "Create Tax"}</button>
              </form>
            </div>
            <div className="card">
              <h3>Tax Profiles</h3>
              <table>
                <thead><tr><th>Name</th><th>CGST</th><th>SGST</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {taxProfiles.map((t) => (
                    <tr key={t.id}>
                      <td>{t.name}</td><td>{t.cgst_rate}%</td><td>{t.sgst_rate}%</td><td>{t.is_active ? "Active" : "Inactive"}</td>
                      <td><button onClick={() => setTaxForm({ ...t })}>Edit</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "pos" && (
          <section className="grid2">
            <div className="card">
              <h3>POS Billing - Bill podalama?</h3>
              <form onSubmit={createInvoice} className="form-grid">
                <select value={invoiceStudentId} onChange={(e) => setInvoiceStudentId(e.target.value)}>
                  <option value="">Walk-in / No Student</option>
                  {students.map((s) => <option key={s.id} value={s.id}>{s.student_code} - {s.first_name}</option>)}
                </select>
                <button type="button" onClick={addInvoiceItemRow}>+ Add Item</button>
                {invoiceItems.map((item, idx) => (
                  <div key={idx} className="row">
                    <select value={item.product_id} onChange={(e) => setInvoiceItems((prev) => prev.map((r, i) => i === idx ? { ...r, product_id: e.target.value } : r))}>
                      <option value="">Select Product</option>
                      {products.map((p) => <option key={p.id} value={p.id}>{p.sku} - {p.name} (Stock {p.stock_on_hand})</option>)}
                    </select>
                    <input type="number" min="1" value={item.quantity} onChange={(e) => setInvoiceItems((prev) => prev.map((r, i) => i === idx ? { ...r, quantity: e.target.value } : r))} />
                    <button type="button" className="danger" onClick={() => setInvoiceItems((prev) => prev.filter((_, i) => i !== idx))}>x</button>
                  </div>
                ))}
                <select value={discountType} onChange={(e) => setDiscountType(e.target.value)}>
                  <option value="">No Discount</option>
                  <option value="percent">percent</option>
                  <option value="flat">flat</option>
                </select>
                <input type="number" step="0.01" placeholder="Discount value" value={discountValue} onChange={(e) => setDiscountValue(e.target.value)} />
                <input placeholder="Payment mode" value={paymentMode} onChange={(e) => setPaymentMode(e.target.value)} />
                <input placeholder="Payment ref" value={paymentReference} onChange={(e) => setPaymentReference(e.target.value)} />
                <div className="card">
                  <p>Subtotal: Rs {money(invoicePreview.subtotal)}</p>
                  <p>Tax: Rs {money(invoicePreview.tax)}</p>
                  <p>Discount: Rs {money(invoicePreview.discountAmount)}</p>
                  <h4>Grand Total: Rs {money(invoicePreview.grandTotal)}</h4>
                </div>
                <button type="submit">Create Invoice</button>
              </form>
            </div>
            <div className="card">
              <h3>Last Invoice Result</h3>
              {!invoiceResult ? <p className="muted">No invoice yet.</p> : (
                <div>
                  <p><strong>Invoice:</strong> {invoiceResult.invoice_no}</p>
                  <p><strong>Grand Total:</strong> Rs {money(invoiceResult.grand_total)}</p>
                  <p><strong>Status:</strong> {invoiceResult.payment_status}</p>
                  <h4>Items</h4>
                  <table>
                    <thead><tr><th>SKU</th><th>Name</th><th>Qty</th><th>Total</th></tr></thead>
                    <tbody>
                      {invoiceResult.items?.map((it) => (
                        <tr key={it.id}><td>{it.sku}</td><td>{it.name}</td><td>{it.quantity}</td><td>{money(it.line_total)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        )}

        {tab === "reports" && (
          <section className="grid2">
            <div className="card">
              <h3>Sales & Fees Summary</h3>
              <p>Invoices: {salesSummary.invoices}</p>
              <p>Sales Total: Rs {money(salesSummary.sales_total)}</p>
              <p>Tax Total: Rs {money(salesSummary.tax_total)}</p>
              <p>Receipts: {feeSummary.receipts}</p>
              <p>Fee Total: Rs {money(feeSummary.fee_total)}</p>
              <button onClick={loadDashboard}>Reload Reports</button>
            </div>
            <div className="card">
              <h3>Most Sold + Peak Hours</h3>
              <h4>Most Sold</h4>
              <ul>{mostSold.map((m) => <li key={m.sku}>{m.name} - {m.quantity}</li>)}</ul>
              <h4>Peak Hours</h4>
              <ul>{peakHours.map((p) => <li key={p.hour}>{p.hour}:00 - {p.count} invoices</li>)}</ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;

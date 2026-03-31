"use client";

import { useEffect, useState, type FormEvent } from "react";

import {
  ApiError,
  assignPlanToUser,
  changeUserRole,
  createManagedUser,
  createPlan,
  deletePlan,
  fetchAdminStats,
  fetchCurrentUser,
  fetchCurrentUserPlan,
  fetchHealth,
  fetchPlans,
  fetchUsers,
  loginUser,
  updatePlan,
  updateUserAddress,
} from "@/lib/api";
import type {
  AddressFormState,
  AdminCreateUserFormState,
  AdminStatsResponse,
  HealthResponse,
  LoginFormState,
  Plan,
  PlanCreateFormState,
  User,
  UserPlanResponse,
  UserRole,
} from "@/lib/types";

type TelecomConsoleProps = { apiBaseUrl: string };

const ACCESS_TOKEN_KEY = "telecom_api.access_token";
const REFRESH_TOKEN_KEY = "telecom_api.refresh_token";

const emptyLogin: LoginFormState = { email: "", password: "" };
const emptyManagedUser: AdminCreateUserFormState = {
  name: "",
  email: "",
  phone: "",
  password: "",
  street: "",
  neighborhood: "",
  address_number: "",
  address_complement: "",
  cep: "",
  role: "user",
};
const emptyPlan: PlanCreateFormState = { name: "", price: "", speed: "" };
const emptyAddressForm: AddressFormState = {
  street: "",
  neighborhood: "",
  address_number: "",
  address_complement: "",
  cep: "",
};

function errorText(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Falha inesperada na interface.";
}

function formatAddress(user: Pick<User, "street" | "neighborhood" | "address_number" | "address_complement" | "cep">): string {
  const primary = [user.street, user.address_number].filter(Boolean).join(", ");
  const secondary = [user.neighborhood, user.address_complement, user.cep].filter(Boolean).join(" | ");
  const parts = [primary, secondary].filter(Boolean);
  return parts.length ? parts.join(" - ") : "nao informado";
}

export function TelecomConsole({ apiBaseUrl }: TelecomConsoleProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentPlan, setCurrentPlan] = useState<UserPlanResponse | null>(null);
  const [adminStats, setAdminStats] = useState<AdminStatsResponse | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedPlanByUser, setSelectedPlanByUser] = useState<Record<number, string>>({});
  const [loginForm, setLoginForm] = useState<LoginFormState>(emptyLogin);
  const [managedUserForm, setManagedUserForm] = useState<AdminCreateUserFormState>(emptyManagedUser);
  const [editingAddressUserId, setEditingAddressUserId] = useState<number | null>(null);
  const [addressForm, setAddressForm] = useState<AddressFormState>(emptyAddressForm);
  const [planForm, setPlanForm] = useState<PlanCreateFormState>(emptyPlan);
  const [editingPlanId, setEditingPlanId] = useState<number | null>(null);
  const [editingPlanForm, setEditingPlanForm] = useState<PlanCreateFormState>(emptyPlan);
  const [accessToken, setAccessToken] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [busyPlanId, setBusyPlanId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState("Preparando a operacao...");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showManagedUserPassword, setShowManagedUserPassword] = useState(false);

  const isAdmin = currentUser?.role === "admin";
  const statusTone = !health ? "warming" : health.status === "healthy" ? "live" : "warning";
  const usersWithPlans = users.filter((user) => user.plan_id !== null);

  useEffect(() => {
    const savedToken = window.sessionStorage.getItem(ACCESS_TOKEN_KEY) || "";
    if (savedToken) setAccessToken(savedToken);

    Promise.all([fetchHealth(apiBaseUrl), fetchPlans(apiBaseUrl)])
      .then(([healthData, plansData]) => {
        setHealth(healthData);
        setPlans(plansData.data);
        setStatusMessage("Base sincronizada.");
      })
      .catch((error) => {
        setErrorMessage(errorText(error));
        setStatusMessage("Falha ao sincronizar a base.");
      });
  }, [apiBaseUrl]);

  useEffect(() => {
    if (!accessToken) {
      setCurrentUser(null);
      setCurrentPlan(null);
      setAdminStats(null);
      setUsers([]);
      window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
      window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
      return;
    }

    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    fetchCurrentUser(accessToken, apiBaseUrl)
      .then(async (user) => {
        setCurrentUser(user);
        setErrorMessage(null);

        if (user.role === "admin") {
          const [stats, listedUsers, planList] = await Promise.all([
            fetchAdminStats(accessToken, apiBaseUrl),
            fetchUsers(accessToken, apiBaseUrl),
            fetchPlans(apiBaseUrl),
          ]);
          setCurrentPlan(null);
          setAdminStats(stats);
          setUsers(listedUsers.data);
          setPlans(planList.data);
          setSelectedPlanByUser(
            Object.fromEntries(
              listedUsers.data.map((listedUser) => [
                listedUser.id,
                listedUser.plan_id ? String(listedUser.plan_id) : "",
              ]),
            ),
          );
          setStatusMessage("Painel administrativo carregado.");
          return;
        }

        try {
          setAdminStats(null);
          setUsers([]);
          const plan = await fetchCurrentUserPlan(accessToken, apiBaseUrl);
          setCurrentPlan(plan);
          setStatusMessage("Area do cliente carregada.");
        } catch {
          setCurrentPlan(null);
          setStatusMessage("Area do cliente carregada sem plano vinculado.");
        }
      })
      .catch((error) => {
        setAccessToken("");
        setErrorMessage(errorText(error));
        setStatusMessage("A sessao nao pode ser reaproveitada.");
      });
  }, [accessToken, apiBaseUrl]);

  async function refreshAdminData() {
    const [stats, listedUsers, planList] = await Promise.all([
      fetchAdminStats(accessToken, apiBaseUrl),
      fetchUsers(accessToken, apiBaseUrl),
      fetchPlans(apiBaseUrl),
    ]);
    setAdminStats(stats);
    setUsers(listedUsers.data);
    setPlans(planList.data);
    setSelectedPlanByUser(
      Object.fromEntries(
        listedUsers.data.map((listedUser) => [
          listedUser.id,
          listedUser.plan_id ? String(listedUser.plan_id) : "",
        ]),
      ),
    );
  }

  async function onLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatusMessage("Autenticando...");
    setErrorMessage(null);
    try {
      const session = await loginUser(loginForm, apiBaseUrl);
      setAccessToken(session.access_token);
      window.sessionStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token);
      setStatusMessage("Sessao iniciada.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Falha no login.");
    }
  }

  async function onCreateManagedUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatusMessage("Criando conta pelo painel...");
    setErrorMessage(null);
    try {
      await createManagedUser(managedUserForm, accessToken, apiBaseUrl);
      setManagedUserForm(emptyManagedUser);
      await refreshAdminData();
      setStatusMessage("Conta criada com sucesso.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel criar a conta.");
    }
  }

  async function onCreatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatusMessage("Criando plano...");
    setErrorMessage(null);
    try {
      await createPlan(planForm, accessToken, apiBaseUrl);
      setPlanForm(emptyPlan);
      await refreshAdminData();
      setStatusMessage("Plano criado com sucesso.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel criar o plano.");
    }
  }

  async function onDeletePlan(planId: number) {
    setBusyPlanId(planId);
    setErrorMessage(null);
    setStatusMessage("Excluindo plano...");
    try {
      await deletePlan(planId, accessToken, apiBaseUrl);
      await refreshAdminData();
      setCurrentPlan((current) => (current?.plan.id === planId ? null : current));
      setStatusMessage("Plano excluido com sucesso.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel excluir o plano.");
    } finally {
      setBusyPlanId(null);
    }
  }

  async function onUpdatePlan(planId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyPlanId(planId);
    setErrorMessage(null);
    setStatusMessage("Salvando alteracoes do plano...");
    try {
      await updatePlan(planId, editingPlanForm, accessToken, apiBaseUrl);
      await refreshAdminData();
      setEditingPlanId(null);
      setEditingPlanForm(emptyPlan);
      setStatusMessage("Plano atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel atualizar o plano.");
    } finally {
      setBusyPlanId(null);
    }
  }

  async function onUpdateAddress(userId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyId(userId);
    setErrorMessage(null);
    setStatusMessage("Atualizando endereco...");
    try {
      await updateUserAddress(userId, addressForm, accessToken, apiBaseUrl);
      await refreshAdminData();
      setEditingAddressUserId(null);
      setAddressForm(emptyAddressForm);
      setStatusMessage("Endereco atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel atualizar o endereco.");
    } finally {
      setBusyId(null);
    }
  }

  async function onChangeRole(userId: number, role: UserRole) {
    setBusyId(userId);
    try {
      await changeUserRole(userId, role, accessToken, apiBaseUrl);
      await refreshAdminData();
      setStatusMessage("Papel atualizado.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel alterar o papel.");
    } finally {
      setBusyId(null);
    }
  }

  async function onAssignPlan(userId: number) {
    const selectedPlanId = selectedPlanByUser[userId];
    if (!selectedPlanId) {
      setErrorMessage("Escolha um plano para o usuario.");
      return;
    }
    setBusyId(userId);
    try {
      await assignPlanToUser(userId, Number(selectedPlanId), accessToken, apiBaseUrl);
      await refreshAdminData();
      setStatusMessage("Plano vinculado ao usuario.");
    } catch (error) {
      setErrorMessage(errorText(error));
      setStatusMessage("Nao foi possivel vincular o plano.");
    } finally {
      setBusyId(null);
    }
  }

  function logout() {
    setAccessToken("");
    setStatusMessage("Sessao encerrada.");
    setErrorMessage(null);
  }

  return (
    <main className="studio-shell">
      <section className="masthead">
        <div className="masthead-copy">
          <span className={`status-chip status-chip--${statusTone}`}>
            {health?.status ?? "warming"} | {currentUser?.role ?? "guest"}
          </span>
          <p className="eyebrow">Telecom API Console</p>
          <h1>Visitante, admin e usuario com jornadas realmente separadas.</h1>
          <p className="masthead-text">As contas agora nascem somente pelo admin. O cliente entra com credenciais provisionadas e visualiza seus dados, endereco e plano sem conseguir editar informacoes sensiveis.</p>
          <div className="base-callout">
            <span className="base-label">Base publica conectada</span>
            <strong className="mono-text">{apiBaseUrl}</strong>
          </div>
        </div>

        <div className="summary-grid">
          <MetricCard label="Saude" value={health?.status ?? "loading"} detail="Estado da API" />
          <MetricCard label="Planos" value={String(plans.length)} detail="Catalogo disponivel" />
          <MetricCard label="Sessao" value={currentUser?.role ?? "guest"} detail={currentUser?.email ?? "Sem usuario autenticado"} />
        </div>
      </section>

      <section className="workspace-grid">
        <div className="workspace-main">
          {!currentUser ? (
            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="section-label">Entrada</p>
                  <h2>Login da plataforma</h2>
                </div>
                <p className="section-note">As contas sao criadas exclusivamente pelo administrador. O cliente entra com os dados recebidos.</p>
              </div>
              <div className="forms-grid">
                <section className="form-panel form-panel--accent">
                  <div className="mini-heading"><p className="section-label">Login</p><h3>Entrar</h3></div>
                  <form className="stack-form" onSubmit={onLogin}>
                    <input type="email" value={loginForm.email} onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))} placeholder="Insira seu email" required />
                    <div className="password-field">
                      <input type={showLoginPassword ? "text" : "password"} value={loginForm.password} onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))} placeholder="Insira sua senha" required />
                      <PasswordToggleButton visible={showLoginPassword} onClick={() => setShowLoginPassword((current) => !current)} />
                    </div>
                    <button className="action-button action-button--dark" type="submit">Autenticar</button>
                  </form>
                </section>
                <section className="form-panel">
                  <div className="mini-heading"><p className="section-label">Acesso do cliente</p><h3>Como funciona</h3></div>
                  <div className="rule-list">
                    <div className="rule-card"><strong>1. Admin cria a conta</strong><p>O administrador registra nome, telefone, endereco e senha inicial do cliente.</p></div>
                    <div className="rule-card"><strong>2. Admin vincula o plano</strong><p>Depois da criacao, o admin escolhe o plano ideal para aquele cliente.</p></div>
                    <div className="rule-card"><strong>3. Cliente apenas acessa</strong><p>Ao entrar, o cliente visualiza seus dados e o plano contratado em modo leitura.</p></div>
                  </div>
                </section>
              </div>
            </article>
          ) : null}

          {currentUser && isAdmin ? (
            <>
              <article className="panel panel--hero">
                <div className="panel-heading">
                  <div><p className="section-label">Admin</p><h2>Controle operacional</h2></div>
                  <button className="ghost-button" type="button" onClick={logout}>Sair</button>
                </div>
                <div className="admin-stats-grid">
                  <MetricCard label="Usuarios" value={String(adminStats?.total_users ?? 0)} detail="Base total" />
                  <MetricCard label="Admins" value={String(adminStats?.total_admins ?? 0)} detail="Acesso elevado" />
                  <MetricCard label="Com plano" value={String(adminStats?.users_with_plan ?? 0)} detail="Assinaturas ativas" />
                  <MetricCard label="Sem plano" value={String(adminStats?.users_without_plan ?? 0)} detail="Aguardando vinculacao" />
                </div>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div><p className="section-label">Cadastro interno</p><h2>Criar contas e planos</h2></div>
                </div>
                <div className="forms-grid">
                  <section className="form-panel">
                    <div className="mini-heading"><p className="section-label">Conta</p><h3>Novo usuario ou admin</h3></div>
                    <form className="stack-form" onSubmit={onCreateManagedUser}>
                      <input value={managedUserForm.name} onChange={(event) => setManagedUserForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nome do operador" required />
                      <input type="email" value={managedUserForm.email} onChange={(event) => setManagedUserForm((current) => ({ ...current, email: event.target.value }))} placeholder="Insira seu email" required />
                      <input value={managedUserForm.phone} onChange={(event) => setManagedUserForm((current) => ({ ...current, phone: event.target.value }))} placeholder="11988887777" />
                      <input value={managedUserForm.street ?? ""} onChange={(event) => setManagedUserForm((current) => ({ ...current, street: event.target.value }))} placeholder="Rua" />
                      <input value={managedUserForm.neighborhood ?? ""} onChange={(event) => setManagedUserForm((current) => ({ ...current, neighborhood: event.target.value }))} placeholder="Bairro" />
                      <div className="inline-field-grid">
                        <input value={managedUserForm.address_number ?? ""} onChange={(event) => setManagedUserForm((current) => ({ ...current, address_number: event.target.value }))} placeholder="Numero" />
                        <input value={managedUserForm.cep ?? ""} onChange={(event) => setManagedUserForm((current) => ({ ...current, cep: event.target.value }))} placeholder="CEP" />
                      </div>
                      <input value={managedUserForm.address_complement ?? ""} onChange={(event) => setManagedUserForm((current) => ({ ...current, address_complement: event.target.value }))} placeholder="Complemento" />
                      <div className="password-field">
                        <input type={showManagedUserPassword ? "text" : "password"} value={managedUserForm.password} onChange={(event) => setManagedUserForm((current) => ({ ...current, password: event.target.value }))} placeholder="Insira sua senha" required />
                        <PasswordToggleButton visible={showManagedUserPassword} onClick={() => setShowManagedUserPassword((current) => !current)} />
                      </div>
                      <select value={managedUserForm.role} onChange={(event) => setManagedUserForm((current) => ({ ...current, role: event.target.value as UserRole }))}>
                        <option value="user">Usuario</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button className="action-button" type="submit">Criar conta</button>
                    </form>
                  </section>
                  <section className="form-panel form-panel--accent">
                    <div className="mini-heading"><p className="section-label">Plano</p><h3>Novo produto</h3></div>
                    <form className="stack-form" onSubmit={onCreatePlan}>
                      <input value={planForm.name} onChange={(event) => setPlanForm((current) => ({ ...current, name: event.target.value }))} placeholder="Fibra Max" required />
                      <input value={planForm.price} onChange={(event) => setPlanForm((current) => ({ ...current, price: event.target.value }))} placeholder="149.90" required />
                      <input value={planForm.speed} onChange={(event) => setPlanForm((current) => ({ ...current, speed: event.target.value }))} placeholder="800" required />
                      <button className="action-button action-button--dark" type="submit">Criar plano</button>
                    </form>
                  </section>
                </div>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div><p className="section-label">Gestao</p><h2>Usuarios cadastrados</h2></div>
                  <span className="pill-accent">{users.length} contas</span>
                </div>
                <div className="user-management-list">
                  {users.map((user) => (
                    <div key={user.id} className="user-card">
                      <div className="user-card-head">
                        <div><strong>{user.name}</strong><p>{user.email}</p></div>
                        <span className={`role-pill role-pill--${user.role}`}>{user.role}</span>
                      </div>
                      <div className="user-meta-grid">
                        <InfoRow label="Telefone" value={user.phone ?? "nao informado"} />
                        <InfoRow label="Plano" value={user.plan_id ? plans.find((plan) => plan.id === user.plan_id)?.name ?? "vinculado" : "sem plano"} />
                        <InfoRow label="Endereco" value={formatAddress(user)} />
                      </div>
                      <div className="user-actions">
                        <button className="ghost-button" type="button" disabled={user.id === currentUser.id || busyId === user.id} onClick={() => onChangeRole(user.id, user.role === "admin" ? "user" : "admin")}>
                          {user.id === currentUser.id ? "Admin atual" : user.role === "admin" ? "Tornar usuario" : "Promover a admin"}
                        </button>
                        <div className="plan-assigner">
                          <select value={selectedPlanByUser[user.id] ?? ""} onChange={(event) => setSelectedPlanByUser((current) => ({ ...current, [user.id]: event.target.value }))}>
                            <option value="">Escolha um plano</option>
                            {plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name}</option>)}
                          </select>
                          <button className="action-button action-button--small" type="button" disabled={busyId === user.id} onClick={() => onAssignPlan(user.id)}>Salvar plano</button>
                        </div>
                      </div>
                      <div className="address-editor">
                        {editingAddressUserId === user.id ? (
                          <form className="edit-plan-form" onSubmit={(event) => onUpdateAddress(user.id, event)}>
                            <input value={addressForm.street} onChange={(event) => setAddressForm((current) => ({ ...current, street: event.target.value }))} placeholder="Rua" />
                            <input value={addressForm.neighborhood} onChange={(event) => setAddressForm((current) => ({ ...current, neighborhood: event.target.value }))} placeholder="Bairro" />
                            <div className="inline-field-grid">
                              <input value={addressForm.address_number} onChange={(event) => setAddressForm((current) => ({ ...current, address_number: event.target.value }))} placeholder="Numero" />
                              <input value={addressForm.cep} onChange={(event) => setAddressForm((current) => ({ ...current, cep: event.target.value }))} placeholder="CEP" />
                            </div>
                            <input value={addressForm.address_complement} onChange={(event) => setAddressForm((current) => ({ ...current, address_complement: event.target.value }))} placeholder="Complemento" />
                            <div className="edit-plan-actions">
                              <button className="action-button action-button--small" type="submit" disabled={busyId === user.id}>Salvar endereco</button>
                              <button className="ghost-button" type="button" onClick={() => { setEditingAddressUserId(null); setAddressForm(emptyAddressForm); }}>Cancelar</button>
                            </div>
                          </form>
                        ) : (
                          <button
                            className="ghost-button"
                            type="button"
                            onClick={() => {
                              setEditingAddressUserId(user.id);
                              setAddressForm({
                                street: user.street ?? "",
                                neighborhood: user.neighborhood ?? "",
                                address_number: user.address_number ?? "",
                                address_complement: user.address_complement ?? "",
                                cep: user.cep ?? "",
                              });
                            }}
                          >
                            Editar endereco
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div><p className="section-label">Clientes com plano</p><h2>Assinaturas ativas</h2></div>
                  <span className="pill-accent">{usersWithPlans.length} clientes</span>
                </div>
                <div className="user-management-list">
                  {usersWithPlans.length ? usersWithPlans.map((user) => (
                    <div key={`subscriber-${user.id}`} className="user-card">
                      <div className="user-card-head">
                        <div>
                          <strong>{user.name}</strong>
                          <p>{user.email}</p>
                        </div>
                        <span className="role-pill role-pill--adminish">
                          {plans.find((plan) => plan.id === user.plan_id)?.name ?? "Plano vinculado"}
                        </span>
                      </div>
                      <div className="user-meta-grid">
                        <InfoRow label="Telefone" value={user.phone ?? "nao informado"} />
                        <InfoRow
                          label="Velocidade"
                          value={
                            user.plan_id
                              ? `${plans.find((plan) => plan.id === user.plan_id)?.speed ?? "--"} Mbps`
                              : "sem plano"
                          }
                        />
                      </div>
                    </div>
                  )) : (
                    <div className="empty-state">
                      <strong>Nenhuma assinatura ativa.</strong>
                      <p>Associe um plano a algum usuario para acompanhar os clientes ativos aqui.</p>
                    </div>
                  )}
                </div>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div><p className="section-label">Catalogo atual</p><h2>Planos publicados</h2></div>
                  <span className="pill-accent">{plans.length} planos</span>
                </div>
                <div className="user-management-list">
                  {plans.map((plan) => (
                    <div key={plan.id} className="user-card">
                      <div className="user-card-head">
                        <div><strong>{plan.name}</strong><p>{plan.speed} Mbps</p></div>
                        <span className="role-pill role-pill--user">R$ {plan.price.toFixed(2)}</span>
                      </div>
                      <div className="linked-customers">
                        <strong>Clientes neste plano</strong>
                        {users.filter((user) => user.plan_id === plan.id).length ? (
                          <div className="linked-customer-list">
                            {users
                              .filter((user) => user.plan_id === plan.id)
                              .map((user) => (
                                <div key={`plan-${plan.id}-user-${user.id}`} className="linked-customer-chip">
                                  <span>{user.name}</span>
                                  <small>{user.email}</small>
                                </div>
                              ))}
                          </div>
                        ) : (
                          <p>Nenhum cliente vinculado no momento.</p>
                        )}
                      </div>
                      <div className="user-actions">
                        {editingPlanId === plan.id ? (
                          <form className="edit-plan-form" onSubmit={(event) => onUpdatePlan(plan.id, event)}>
                            <input value={editingPlanForm.name} onChange={(event) => setEditingPlanForm((current) => ({ ...current, name: event.target.value }))} placeholder="Nome do plano" required />
                            <input value={editingPlanForm.price} onChange={(event) => setEditingPlanForm((current) => ({ ...current, price: event.target.value }))} placeholder="Preco" required />
                            <input value={editingPlanForm.speed} onChange={(event) => setEditingPlanForm((current) => ({ ...current, speed: event.target.value }))} placeholder="Velocidade" required />
                            <div className="edit-plan-actions">
                              <button className="action-button action-button--small" type="submit" disabled={busyPlanId === plan.id}>
                                {busyPlanId === plan.id ? "Salvando..." : "Salvar"}
                              </button>
                              <button className="ghost-button" type="button" onClick={() => setEditingPlanId(null)}>
                                Cancelar
                              </button>
                            </div>
                          </form>
                        ) : (
                          <>
                            <div className="rule-card rule-card--compact">
                              <strong>Impacto da exclusao</strong>
                              <p>Usuarios vinculados a esse plano ficarao sem plano ativo.</p>
                            </div>
                            <div className="catalog-actions">
                              <button
                                className="ghost-button"
                                type="button"
                                onClick={() => {
                                  setEditingPlanId(plan.id);
                                  setEditingPlanForm({
                                    name: plan.name,
                                    price: String(plan.price),
                                    speed: String(plan.speed),
                                  });
                                }}
                              >
                                Editar plano
                              </button>
                              <button className="ghost-button ghost-button--danger" type="button" disabled={busyPlanId === plan.id} onClick={() => onDeletePlan(plan.id)}>
                                {busyPlanId === plan.id ? "Excluindo..." : "Excluir plano"}
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            </>
          ) : null}

          {currentUser && !isAdmin ? (
            <>
              <article className="panel panel--hero">
                <div className="panel-heading">
                  <div><p className="section-label">Cliente</p><h2>Seu plano e seu acesso</h2></div>
                  <button className="ghost-button" type="button" onClick={logout}>Sair</button>
                </div>
                <div className="client-summary-grid">
                  <div className="profile-card">
                    <div className="profile-top">
                      <div className="avatar-badge">{currentUser.name.slice(0, 1).toUpperCase()}</div>
                      <div><strong>{currentUser.name}</strong><p>{currentUser.email}</p></div>
                    </div>
                    <div className="info-stack">
                      <InfoRow label="Papel" value={currentUser.role} />
                      <InfoRow label="Telefone" value={currentUser.phone ?? "nao informado"} />
                      <InfoRow label="Endereco" value={formatAddress(currentUser)} />
                    </div>
                  </div>
                  <div className="profile-card profile-card--plan">
                    <p className="section-label">Plano do usuario</p>
                    <strong className="plan-highlight">{currentPlan?.plan.name ?? "Nenhum plano vinculado"}</strong>
                    <p className="plan-highlight-text">
                      {currentPlan ? `${currentPlan.plan.speed} Mbps por R$ ${currentPlan.plan.price.toFixed(2)} ao mes.` : "Um admin precisa associar um plano para liberar esta visao."}
                    </p>
                  </div>
                </div>
              </article>
              <article className="panel panel--hero">
                <div className="panel-heading">
                  <div><p className="section-label">Catalogo</p><h2>Planos disponiveis</h2></div>
                </div>
                <div className="plan-list">
                  {plans.map((plan) => (
                    <div key={plan.id} className="plan-row">
                      <div className="plan-main"><strong>{plan.name}</strong><p>{plan.speed} Mbps de velocidade nominal</p></div>
                      <div className="plan-price"><span>Mensal</span><strong>R$ {plan.price.toFixed(2)}</strong></div>
                    </div>
                  ))}
                </div>
              </article>
            </>
          ) : null}
        </div>

        <aside className="workspace-side">
          <article className="panel">
            <div className="panel-heading"><div><p className="section-label">Operacao</p><h2>Diario do painel</h2></div></div>
            <div className="journal">
              <div className="journal-entry"><span className="journal-dot" /><div><strong>Status atual</strong><p>{statusMessage}</p></div></div>
              {errorMessage ? <div className="journal-entry journal-entry--error"><span className="journal-dot" /><div><strong>Ultimo erro</strong><p>{errorMessage}</p></div></div> : <div className="journal-entry"><span className="journal-dot journal-dot--soft" /><div><strong>Sem bloqueios</strong><p>Nenhum erro recente foi registrado.</p></div></div>}
            </div>
          </article>
          <article className="panel">
            <div className="panel-heading"><div><p className="section-label">Hierarquia</p><h2>Niveis de acesso</h2></div></div>
            <div className="rule-list">
              <div className="rule-card"><strong>Visitante</strong><p>Consulta planos publicos, cria conta e faz login.</p></div>
              <div className="rule-card"><strong>Usuario</strong><p>Enxerga apenas o proprio perfil e o plano vinculado.</p></div>
              <div className="rule-card"><strong>Admin</strong><p>Cria usuarios, promove admins, publica planos e associa assinaturas.</p></div>
            </div>
          </article>
          <article className="panel">
            <div className="panel-heading"><div><p className="section-label">Infra</p><h2>Snapshot da API</h2></div></div>
            <div className="info-stack">
              <InfoRow label="Servico" value={health?.service ?? "telecom-api"} />
              <InfoRow label="Versao" value={health?.version ?? "oculta"} />
              <InfoRow label="Base URL" value={apiBaseUrl} mono />
            </div>
          </article>
        </aside>
      </section>
    </main>
  );
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong><p>{detail}</p></div>;
}

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return <div className="info-row"><span>{label}</span><strong className={mono ? "mono-text" : ""}>{value}</strong></div>;
}

function PasswordToggleButton({
  visible,
  onClick,
}: {
  visible: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="password-visibility-button"
      type="button"
      onClick={onClick}
      aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
      title={visible ? "Ocultar senha" : "Mostrar senha"}
    >
      {visible ? <EyeOffIcon /> : <EyeIcon />}
    </button>
  );
}

function EyeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
      <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.7" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M3 3l18 18"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.7"
      />
      <path
        d="M10.6 6.3A10.9 10.9 0 0 1 12 6c6.5 0 10 6 10 6a17 17 0 0 1-4.1 4.4"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
      <path
        d="M6.2 6.8A17.8 17.8 0 0 0 2 12s3.5 6 10 6c1.5 0 2.8-.3 4-.8"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
      <path
        d="M9.9 9.9A3 3 0 0 0 9 12a3 3 0 0 0 4.6 2.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
    </svg>
  );
}

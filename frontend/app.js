// A API serve estas telas no mesmo endereço. A sessão fica apenas nesta aba.
let token = sessionStorage.getItem("clinica_token");
let dados = {};
const app = document.querySelector("#app");
const escapar = (valor) =>
  String(valor ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c],
  );

async function api(caminho, metodo = "GET", corpo) {
  let resposta;
  try {
    resposta = await fetch(caminho, {
      method: metodo,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
      },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
      signal: AbortSignal.timeout(12000),
    });
  } catch {
    throw new Error(
      "Não foi possível acessar a clínica. Confira a conexão e tente novamente.",
    );
  }
  const conteudo = resposta.status === 204 ? null : await resposta.json();
  if (!resposta.ok) {
    if (resposta.status === 401 && caminho !== "/login") {
      token = null;
      sessionStorage.removeItem("clinica_token");
      login("Sua sessão terminou. Entre novamente.");
    }
    let detalhe = conteudo?.detail;
    if (Array.isArray(detalhe)) {
      detalhe = detalhe
        .map(
          (e) =>
            e.loc.slice(1).join(" / ") +
            ": " +
            e.msg.replace("Value error, ", ""),
        )
        .join("; ");
    }
    throw new Error(detalhe || "Não foi possível concluir a operação.");
  }
  return conteudo;
}

function avisar(texto, erro = false) {
  const caixa = document.querySelector("#aviso");
  if (caixa) {
    caixa.className = "alert " + (erro ? "error" : "success");
    caixa.textContent = texto;
    caixa.focus();
  }
}

function campo(nome, titulo, tipo = "text", obrigatorio = false, extra = "") {
  return (
    "<label>" +
    titulo +
    '<input name="' +
    nome +
    '" type="' +
    tipo +
    '" ' +
    (obrigatorio ? "required " : "") +
    extra +
    "></label>"
  );
}
function texto(nome, titulo) {
  return (
    "<label>" +
    titulo +
    '<textarea name="' +
    nome +
    '" maxlength="10000"></textarea></label>'
  );
}
function seletor(nome, titulo, opcoes, opcional = false) {
  return (
    "<label>" +
    titulo +
    '<select name="' +
    nome +
    '" ' +
    (opcional ? "" : "required") +
    '><option value="">' +
    (opcional ? "Não informado" : "Selecione") +
    "</option>" +
    opcoes
      .map(
        (o) =>
          '<option value="' +
          escapar(o.id) +
          '">' +
          escapar(o.nome || o.nome_completo) +
          "</option>",
      )
      .join("") +
    "</select></label>"
  );
}
function situacoes(valores) {
  return (
    '<label>Situação<select name="situacao">' +
    valores.map((v) => "<option>" + v + "</option>").join("") +
    "</select></label>"
  );
}
function lerFormulario(form) {
  const valores = {};
  for (const [chave, valor] of new FormData(form))
    valores[chave] = valor.trim() || null;
  for (const c of form.querySelectorAll(
    'input[type="number"], select[name$="_id"]',
  )) {
    valores[c.name] = c.value === "" ? null : Number(c.value);
  }
  for (const c of form.querySelectorAll('input[type="checkbox"]'))
    valores[c.name] = c.checked;
  return valores;
}
function enviarFormulario(id, salvar) {
  document.querySelector("#" + id).onsubmit = async (evento) => {
    evento.preventDefault();
    const form = evento.currentTarget;
    const botao = form.querySelector('button[type="submit"]');
    botao.disabled = true;
    try {
      await salvar(lerFormulario(form), form);
    } catch (erro) {
      avisar(erro.message, true);
    } finally {
      botao.disabled = false;
    }
  };
}

function estrutura(titulo, conteudo) {
  app.innerHTML =
    "<header><div><strong>Clínica Veterinária</strong><small>Cadastros e atendimento</small></div>" +
    '<nav aria-label="Menu principal">' +
    [
      ["inicio", "Início"],
      ["tutores", "Tutores"],
      ["animais", "Animais"],
      ["clinica", "Atendimento"],
      ["catalogos", "Espécies e raças"],
    ]
      .map(
        ([p, t]) =>
          '<button data-pagina="' +
          p +
          '" class="secondary">' +
          t +
          "</button>",
      )
      .join("") +
    '<button id="sair" class="secondary">Sair</button></nav></header>' +
    '<div class="container"><h1>' +
    titulo +
    '</h1><div id="aviso" role="status" tabindex="-1"></div>' +
    conteudo +
    "</div>";
  document
    .querySelectorAll("[data-pagina]")
    .forEach((b) => (b.onclick = () => navegar(b.dataset.pagina)));
  document.querySelector("#sair").onclick = async () => {
    try {
      await api("/logout", "POST");
      token = null;
      sessionStorage.removeItem("clinica_token");
      login("Você saiu da sessão.");
    } catch (erro) {
      avisar(erro.message, true);
    }
  };
}
function login(mensagem = "") {
  app.innerHTML =
    '<div class="container"><section class="card login"><p class="muted">Clínica Veterinária</p>' +
    '<h1>Acesso do veterinário</h1><div id="aviso" role="status" tabindex="-1">' +
    escapar(mensagem) +
    "</div>" +
    '<form id="login">' +
    campo("email", "E-mail", "email", true, 'autocomplete="username"') +
    campo(
      "senha",
      "Senha",
      "password",
      true,
      'autocomplete="current-password"',
    ) +
    '<button type="submit">Entrar</button></form></section></div>';
  enviarFormulario("login", async (d) => {
    const sessao = await api("/login", "POST", d);
    token = sessao.token_acesso;
    sessionStorage.setItem("clinica_token", token);
    await navegar("inicio");
  });
}
async function navegar(pagina) {
  if (!token) return login();
  estrutura("Carregando", "<p>Aguarde...</p>");
  try {
    const entidades = ["tutores", "animais", "especies", "racas"];
    const listas = await Promise.all(entidades.map((e) => api("/" + e)));
    entidades.forEach((e, i) => (dados[e] = listas[i]));
    if (token) ({ inicio, tutores, animais, clinica, catalogos })[pagina]();
  } catch (erro) {
    avisar(erro.message, true);
  }
}
const ativos = (lista) =>
  lista.filter((x) => !String(x.situacao).startsWith("INATIV"));
const opcoesAnimais = () =>
  seletor("animal_id", "Animal", ativos(dados.animais));

function inicio() {
  estrutura(
    "Painel da clínica",
    '<div class="grid"><section class="card"><h2>' +
      ativos(dados.tutores).length +
      " tutores</h2><p>Cadastre o responsável e confira o endereço pelo CEP.</p></section>" +
      '<section class="card"><h2>' +
      ativos(dados.animais).length +
      " animais</h2><p>Abra a ficha para consultar os atendimentos e as vacinas.</p></section>" +
      '<section class="card"><h2>Atendimento</h2><p>Os registros ficam vinculados ao veterinário conectado.</p></section></div>',
  );
}
function tutores() {
  estrutura(
    "Tutores",
    '<section class="card"><h2>Novo tutor</h2><form id="tutor"><div class="grid">' +
      campo("nome_completo", "Nome completo", "text", true) +
      campo("cpf", "CPF", "text", true) +
      campo("data_nascimento", "Nascimento", "date", true) +
      campo("email", "E-mail", "email", true) +
      campo("telefone", "Telefone") +
      '</div><fieldset><legend>Endereço</legend><div class="row">' +
      campo(
        "cep",
        "CEP",
        "text",
        true,
        'inputmode="numeric" maxlength="9" placeholder="01001-000"',
      ) +
      '<button type="button" id="buscar-cep">Consultar CEP</button></div><p class="muted">Confira o endereço e complete o número. Todos os campos podem ser editados.</p><div class="grid">' +
      campo("logradouro", "Logradouro", "text", true) +
      campo("numero", "Número", "text", true) +
      campo("complemento", "Complemento") +
      campo("bairro", "Bairro", "text", true) +
      campo("cidade", "Cidade", "text", true) +
      campo("uf", "UF", "text", true, 'maxlength="2"') +
      campo("codigo_ibge", "Código IBGE (opcional)") +
      '</div></fieldset><button type="submit">Cadastrar tutor</button></form></section>' +
      '<section class="card"><h2>Tutores cadastrados</h2>' +
      (dados.tutores
        .map(
          (t) =>
            "<p>" +
            escapar(t.nome_completo) +
            " — " +
            escapar(t.email) +
            " · " +
            escapar(t.situacao) +
            "</p>",
        )
        .join("") || "<p>Nenhum tutor cadastrado.</p>") +
      "</section>",
  );
  const form = document.querySelector("#tutor");
  document.querySelector("#buscar-cep").onclick = async (evento) => {
    const botao = evento.currentTarget;
    const cep = form.elements.cep.value.replace(/\D/g, "");
    if (cep.length !== 8) return avisar("Informe um CEP com 8 dígitos.", true);
    botao.disabled = true;
    try {
      const endereco = await api("/clinica/cep/" + cep);
      if (form.elements.cep.value.replace(/\D/g, "") !== cep) return;
      Object.entries(endereco).forEach(
        ([c, v]) => (form.elements[c].value = v || ""),
      );
      avisar(
        "Endereço preenchido pelo ViaCEP. Complete o número e confira os dados.",
      );
    } catch (erro) {
      avisar(erro.message, true);
    } finally {
      botao.disabled = false;
    }
  };
  enviarFormulario("tutor", async (d) => {
    const endereco = {};
    for (const c of [
      "cep",
      "logradouro",
      "numero",
      "complemento",
      "bairro",
      "cidade",
      "uf",
      "codigo_ibge",
    ]) {
      endereco[c] = d[c];
      delete d[c];
    }
    endereco.cep = endereco.cep.replace(/\D/g, "");
    endereco.uf = endereco.uf.toUpperCase();
    d.cpf = d.cpf.replace(/\D/g, "");
    await api("/clinica/tutores", "POST", { ...d, endereco });
    await navegar("tutores");
    avisar("Tutor cadastrado com sucesso.");
  });
}
function animais() {
  estrutura(
    "Animais",
    '<section class="card"><h2>Novo animal</h2><form id="animal"><div class="grid">' +
      campo("nome", "Nome", "text", true) +
      campo("codigo_rfid", "Código RFID", "text", true, 'maxlength="48"') +
      seletor("tutor_id", "Tutor", ativos(dados.tutores)) +
      seletor("especie_id", "Espécie", ativos(dados.especies)) +
      seletor("raca_id", "Raça (opcional)", [], true) +
      campo("sexo", "Sexo", "text", true) +
      campo("cor", "Cor", "text", true) +
      campo(
        "peso_atual_kg",
        "Peso (kg)",
        "number",
        true,
        'min="0.001" step="0.001"',
      ) +
      campo("data_nascimento", "Nascimento", "date") +
      campo(
        "idade_estimada_meses",
        "Idade estimada (meses)",
        "number",
        false,
        'min="0" step="1"',
      ) +
      '</div><p class="muted">Informe o nascimento ou a idade estimada. O RFID precisa ser único.</p><button type="submit">Cadastrar animal</button></form></section>' +
      '<section class="card"><h2>Fichas dos animais</h2>' +
      (dados.animais
        .map(
          (a) =>
            '<div class="row item"><span>' +
            escapar(a.nome) +
            " · " +
            escapar(a.situacao) +
            '</span><button data-ficha="' +
            a.id +
            '" class="secondary">Ficha de ' +
            escapar(a.nome) +
            "</button></div>",
        )
        .join("") || "<p>Nenhum animal cadastrado.</p>") +
      "</section>",
  );
  const form = document.querySelector("#animal");
  form.elements.especie_id.onchange = () => {
    const racas = ativos(dados.racas).filter(
      (r) => r.especie_id == form.elements.especie_id.value,
    );
    form.elements.raca_id.innerHTML =
      '<option value="">Não informado</option>' +
      racas
        .map(
          (r) =>
            '<option value="' + r.id + '">' + escapar(r.nome) + "</option>",
        )
        .join("");
  };
  enviarFormulario("animal", async (d) => {
    if (d.data_nascimento === null && d.idade_estimada_meses === null)
      throw new Error("Informe o nascimento ou a idade estimada.");
    await api("/animais", "POST", d);
    await navegar("animais");
    avisar("Animal cadastrado e RFID vinculado.");
  });
  document
    .querySelectorAll("[data-ficha]")
    .forEach((b) => (b.onclick = () => ficha(b.dataset.ficha)));
}
const camposConsulta = {
  motivo: "Motivo",
  anamnese: "Anamnese",
  sintomas: "Sintomas",
  diagnostico: "Diagnóstico",
  tratamento_prescrito: "Tratamento",
  prescricao_medicamentos: "Prescrição de medicamentos",
  observacoes: "Observações",
};
function clinica() {
  estrutura(
    "Atendimento",
    '<p>O veterinário responsável é identificado automaticamente pela sessão.</p><div class="grid">' +
      '<section class="card"><h2>Consulta</h2><form id="consulta">' +
      opcoesAnimais() +
      campo("data_hora", "Data e hora da consulta", "datetime-local", true) +
      situacoes(["REALIZADA", "AGENDADA", "CANCELADA"]) +
      Object.entries(camposConsulta)
        .map(([n, t]) => texto(n, t))
        .join("") +
      campo(
        "peso_registrado_kg",
        "Peso registrado (kg)",
        "number",
        false,
        'min="0.001" step="0.001"',
      ) +
      campo(
        "temperatura_c",
        "Temperatura (°C)",
        "number",
        false,
        'min="0.01" max="99.99" step="0.01"',
      ) +
      '<button type="submit">Registrar consulta</button></form></section><section class="card"><h2>Vacina</h2><form id="vacina">' +
      opcoesAnimais() +
      campo("nome_vacina", "Nome da vacina", "text", true) +
      campo("tipo_vacina", "Tipo da vacina") +
      '<label class="checkbox"><input type="checkbox" name="antirrabica"> Vacina antirrábica</label>' +
      situacoes(["APLICADA", "AGENDADA", "CANCELADA"]) +
      campo("fabricante", "Fabricante") +
      campo("numero_lote", "Número do lote") +
      campo("via_aplicacao", "Via de aplicação") +
      campo("dose_etapa", "Dose / etapa") +
      campo("validade_lote", "Validade do lote", "date") +
      campo("data_agendada", "Data agendada", "date") +
      campo("data_aplicacao", "Data de aplicação", "date") +
      campo("proxima_dose_em", "Próxima dose (opcional)", "date") +
      texto("observacoes", "Observações") +
      '<button type="submit">Registrar vacina</button></form></section></div>',
  );
  for (const nome of ["consulta", "vacina"]) {
    enviarFormulario(nome, async (d, form) => {
      await api(
        "/clinica/" + (nome === "consulta" ? "consultas" : "vacinas"),
        "POST",
        d,
      );
      form.reset();
      avisar(
        (nome === "consulta" ? "Consulta" : "Vacina") +
          " registrada. Abra a ficha do animal para conferir.",
      );
    });
  }
}
function detalhes(registro, campos) {
  return (
    "<dl>" +
    Object.entries(campos)
      .filter(([c]) => registro[c] !== null && registro[c] !== "")
      .map(
        ([c, t]) => "<dt>" + t + "</dt><dd>" + escapar(registro[c]) + "</dd>",
      )
      .join("") +
    "</dl>"
  );
}
async function ficha(id) {
  try {
    const h = await api("/clinica/animais/" + id + "/historico");
    const animal = dados.animais.find((a) => a.id == id);
    estrutura(
      "Ficha de " + escapar(animal.nome),
      '<section class="card"><p>RFID: <strong>' +
        escapar(h.microchip?.codigo_rfid || "Não informado") +
        "</strong></p>" +
        detalhes(animal, {
          sexo: "Sexo",
          cor: "Cor",
          peso_atual_kg: "Peso (kg)",
          data_nascimento: "Nascimento",
          idade_estimada_meses: "Idade estimada (meses)",
        }) +
        '</section><section class="card"><h2>Próximas doses e agendamentos</h2><p class="muted">Previsões registradas; confira no histórico se já houve nova aplicação.</p>' +
        (h.proximas_doses
          .map(
            (d) =>
              "<p>" +
              escapar(d.nome_vacina) +
              " · " +
              escapar(d.data_prevista) +
              " · " +
              (d.prazo === "ATRASADA"
                ? "Data prevista já passou"
                : "Prevista") +
              "</p>",
          )
          .join("") || "<p>Nenhuma dose prevista.</p>") +
        '</section><div class="grid"><section class="card"><h2>Histórico de consultas</h2>' +
        (h.consultas
          .map(
            (c) =>
              "<article><h3>" +
              escapar(c.data_hora.replace("T", " ")) +
              " · " +
              escapar(c.situacao) +
              "</h3>" +
              detalhes(c, {
                veterinario_nome: "Veterinário responsável",
                ...camposConsulta,
                peso_registrado_kg: "Peso (kg)",
                temperatura_c: "Temperatura (°C)",
              }) +
              "</article>",
          )
          .join("") || "<p>Nenhuma consulta registrada.</p>") +
        '</section><section class="card"><h2>Histórico de vacinação</h2>' +
        (h.vacinas
          .map(
            (v) =>
              "<article><h3>" +
              escapar(v.nome_vacina) +
              " · " +
              escapar(v.situacao) +
              "</h3><p>Antirrábica: " +
              (v.antirrabica ? "Sim" : "Não") +
              "</p>" +
              detalhes(v, {
                veterinario_nome: "Veterinário responsável",
                tipo_vacina: "Tipo",
                fabricante: "Fabricante",
                numero_lote: "Lote",
                via_aplicacao: "Via",
                dose_etapa: "Dose / etapa",
                validade_lote: "Validade do lote",
                data_agendada: "Agendada para",
                data_aplicacao: "Aplicação",
                proxima_dose_em: "Próxima dose",
                observacoes: "Observações",
              }) +
              "</article>",
          )
          .join("") || "<p>Nenhuma vacina registrada.</p>") +
        "</section></div>",
    );
  } catch (erro) {
    avisar(erro.message, true);
  }
}
function catalogos() {
  estrutura(
    "Espécies e raças",
    '<div class="grid"><section class="card"><h2>Nova espécie</h2><form id="especie">' +
      campo("nome", "Nome da espécie", "text", true) +
      texto("descricao", "Descrição") +
      '<button type="submit">Cadastrar espécie</button></form>' +
      dados.especies.map((e) => "<p>" + escapar(e.nome) + "</p>").join("") +
      '</section><section class="card"><h2>Nova raça</h2><form id="raca">' +
      seletor("especie_id", "Espécie da raça", ativos(dados.especies)) +
      campo("nome", "Nome da raça", "text", true) +
      texto("descricao", "Descrição") +
      '<button type="submit">Cadastrar raça</button></form>' +
      dados.racas
        .map(
          (r) =>
            "<p>" +
            escapar(r.nome) +
            " · " +
            escapar(dados.especies.find((e) => e.id === r.especie_id)?.nome) +
            "</p>",
        )
        .join("") +
      "</section></div>",
  );
  for (const nome of ["especie", "raca"]) {
    enviarFormulario(nome, async (d) => {
      await api("/" + (nome === "especie" ? "especies" : "racas"), "POST", d);
      await navegar("catalogos");
      avisar("Cadastro realizado.");
    });
  }
}
if (token) navegar("inicio");
else login();

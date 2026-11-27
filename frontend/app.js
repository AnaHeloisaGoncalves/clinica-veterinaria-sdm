// A API serve estas telas no mesmo endereço. A sessão fica apenas nesta aba.
let token = sessionStorage.getItem("clinica_token");
let dados = {};
let gestor = false;
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
    const erro = new Error(detalhe || "Não foi possível concluir a operação.");
    erro.status = resposta.status;
    throw erro;
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
function texto(nome, titulo, obrigatorio = false) {
  return (
    "<label>" +
    titulo +
    '<textarea name="' +
    nome +
    '" maxlength="10000"' +
    (obrigatorio ? " required" : "") +
    "></textarea></label>"
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
      ...(gestor ? [["acessos", "Acessos da equipe"]] : []),
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
    '<button type="submit">Entrar</button></form>' +
    '<p><button type="button" class="secondary" id="recuperar-senha">Esqueci minha senha</button></p>' +
    '<p class="muted">Primeiro acesso? Solicite um convite ao gestor da clínica.</p></section></div>';
  document.querySelector("#recuperar-senha").onclick = recuperarSenha;
  enviarFormulario("login", async (d, form) => {
    const sessao = await api("/login", "POST", { ...d, senha: form.elements.senha.value });
    token = sessao.token_acesso;
    sessionStorage.setItem("clinica_token", token);
    await navegar("inicio");
  });
}
async function navegar(pagina) {
  if (!token) return login();
  estrutura("Carregando", "<p>Aguarde...</p>");
  try {
    const perfil = await api("/sessao");
    gestor = perfil.administrador;
    if (pagina === "acessos") {
      dados.regrasAcesso = await api("/regras-nascimento");
      return await acessos();
    }
    const entidades = ["tutores", "animais", "especies", "racas"];
    const listas = await Promise.all(entidades.map((e) => api("/" + e)));
    entidades.forEach((e, i) => (dados[e] = listas[i]));
    if (["tutores", "animais", "clinica"].includes(pagina))
      dados.nascimento = await api("/regras-nascimento");
    if (pagina === "clinica") dados.vacinas = await api("/clinica/catalogo-vacinas");
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
      campo("nome_completo", "Nome completo", "text", true, 'maxlength="150"') +
      campo("cpf", "CPF", "text", true, 'inputmode="numeric" maxlength="14" pattern="[0-9]{11}|[0-9]{3}[.][0-9]{3}[.][0-9]{3}\\x2D[0-9]{2}"') +
      campo("data_nascimento", "Nascimento", "date", true,
        'min="' + nascimentoMinimo(dados.nascimento.limite_tutor_meses) + '" max="' + dados.nascimento.hoje + '"') +
      campo("email", "E-mail", "email", true) +
      campo("telefone", "Telefone", "tel", false, 'maxlength="20" placeholder="(21) 99999-9999"') +
      '</div><fieldset><legend>Endereço</legend><div class="row">' +
      campo(
        "cep",
        "CEP",
        "text",
        true,
        'inputmode="numeric" maxlength="9" pattern="[0-9]{5}\\x2D?[0-9]{3}" placeholder="01001-000"',
      ) +
      '<button type="button" id="buscar-cep">Consultar CEP</button></div><p class="muted">Confira o endereço e complete o número. Todos os campos podem ser editados.</p><div class="grid">' +
      campo("logradouro", "Logradouro", "text", true) +
      campo("numero", "Número", "text", true) +
      campo("complemento", "Complemento") +
      campo("bairro", "Bairro", "text", true) +
      campo("cidade", "Cidade", "text", true) +
      seletor("uf", "UF", dados.nascimento.ufs.map((uf) => ({ id: uf, nome: uf }))) +
      campo("codigo_ibge", "Código IBGE (opcional)", "text", false, 'inputmode="numeric" maxlength="7" pattern="[0-9]{7}"') +
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
    const cepDigitado = form.elements.cep.value.trim();
    const cep = cepDigitado.replace("-", "");
    if (!/^[0-9]{5}-?[0-9]{3}$/.test(cepDigitado)) return avisar("Informe um CEP com 8 dígitos.", true);
    botao.disabled = true;
    try {
      const endereco = await api("/clinica/cep/" + cep);
      if (form.elements.cep.value.trim() !== cepDigitado) return;
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
    endereco.uf = endereco.uf.toUpperCase();
    await api("/clinica/tutores", "POST", { ...d, endereco });
    await navegar("tutores");
    avisar("Tutor cadastrado com sucesso.");
  });
}
function mesesCompletos(nascimento, hoje) {
  const [ano, mes, dia] = nascimento.split("-").map(Number);
  const [anoAtual, mesAtual, diaAtual] = hoje.split("-").map(Number);
  return (anoAtual - ano) * 12 + mesAtual - mes - Number(diaAtual < dia);
}

function nascimentoMinimo(limite) {
  const hoje = dados.nascimento.hoje;
  const [ano, mes, dia] = hoje.split("-").map(Number);
  const mesLimite = mes - 2 - limite;
  const ultimoDia = new Date(Date.UTC(ano, mesLimite + 1, 0)).getUTCDate();
  return new Date(Date.UTC(ano, mesLimite, Math.min(dia, ultimoDia) + 1)).toISOString().slice(0, 10);
}

function animais(edicao = null) {
  const opcoes = (lista, atual) =>
    lista.filter((item) => item.id === atual || !String(item.situacao).startsWith("INATIV"));
  estrutura(
    "Animais",
    '<section class="card"><h2>' + (edicao ? "Editar animal" : "Novo animal") +
      '</h2><form id="animal"><div class="grid">' +
      campo("nome", "Nome", "text", true, 'minlength="2" maxlength="100"') +
      (edicao ? "" : campo("codigo_rfid", "Código RFID", "text", true, 'inputmode="numeric" minlength="15" maxlength="15" pattern="[0-9]{15}" placeholder="15 dígitos"')) +
      seletor("tutor_id", "Tutor", opcoes(dados.tutores, edicao?.tutor_id)) +
      seletor("especie_id", "Espécie", opcoes(dados.especies, edicao?.especie_id)) +
      seletor("raca_id", "Raça (opcional)", [], true) +
      seletor("sexo", "Sexo", Object.entries(dados.nascimento.sexos).map(([id, nome]) => ({ id, nome }))) +
      seletor("cor", "Cor", dados.nascimento.cores.map((nome) => ({ id: nome.toLowerCase(), nome }))) +
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
      '</div><p class="muted">A idade em meses é calculada pelo nascimento. Se a data for desconhecida, informe uma estimativa.</p><button type="submit">' +
      (edicao ? "Salvar alterações" : "Cadastrar animal") + "</button>" +
      (edicao ? ' <button type="button" class="secondary" id="cancelar-edicao">Cancelar</button>' : "") +
      "</form></section>" +
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
            "</button>" +
            '<button class="secondary" data-editar="' + a.id + '">Editar ' +
            escapar(a.nome) + "</button></div>",
        )
        .join("") || "<p>Nenhum animal cadastrado.</p>") +
      "</section>",
  );
  const form = document.querySelector("#animal");
  const atualizarRacas = () => {
    const racas = opcoes(dados.racas, edicao?.raca_id).filter(
      (r) => r.especie_id == form.elements.especie_id.value,
    );
    form.elements.raca_id.innerHTML =
      '<option value="">Sem raça definida</option>' +
      racas
        .map(
          (r) =>
            '<option value="' + r.id + '">' + escapar(r.nome) + "</option>",
        )
        .join("");
  };
  const nascimento = form.elements.data_nascimento;
  const idade = form.elements.idade_estimada_meses;
  function atualizarIdade() {
    const limite = dados.nascimento.limite_animal_meses[form.elements.especie_id.value];
    if (limite) {
      nascimento.min = nascimentoMinimo(limite);
      idade.max = limite;
    } else {
      nascimento.removeAttribute("min");
      idade.removeAttribute("max");
    }
    nascimento.max = dados.nascimento.hoje;
    idade.readOnly = Boolean(nascimento.value);
    if (nascimento.value) {
      const meses = mesesCompletos(nascimento.value, dados.nascimento.hoje);
      idade.value = meses >= 0 ? meses : "";
    }
  }
  form.elements.especie_id.onchange = () => {
    atualizarRacas();
    atualizarIdade();
  };
  nascimento.oninput = () => {
    if (!nascimento.value && idade.readOnly) idade.value = "";
    atualizarIdade();
  };
  if (edicao) {
    for (const campo of form.elements) {
      if (campo.name && campo.name !== "raca_id") campo.value = campo.name === "cor" ? String(edicao.cor ?? "").toLowerCase() : edicao[campo.name] ?? "";
    }
    document.querySelector("#cancelar-edicao").onclick = () => animais();
  }
  atualizarRacas();
  atualizarIdade();
  if (edicao) form.elements.raca_id.value = edicao.raca_id ?? "";
  document.querySelectorAll("[data-editar]").forEach((botao) => {
    botao.onclick = () => {
      animais(dados.animais.find((animal) => animal.id === Number(botao.dataset.editar)));
      document.querySelector("#animal").elements.nome.focus();
    };
  });
  enviarFormulario("animal", async (d) => {
    if (d.data_nascimento === null && d.idade_estimada_meses === null)
      throw new Error("Informe o nascimento ou a idade estimada.");
    await api(edicao ? "/animais/" + edicao.id : "/animais", edicao ? "PUT" : "POST", d);
    await navegar("animais");
    avisar(edicao ? "Animal atualizado com sucesso." : "Animal cadastrado e RFID vinculado.");
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
      situacoes(["REALIZADA", "AGENDADA", "CANCELADA", "NAO_COMPARECEU"]) +
      Object.entries(camposConsulta)
        .map(([n, t]) => texto(n, t, n === "motivo"))
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
      '<label>Nome da vacina<select name="vacina_codigo" required></select></label>' +
      '<p id="tipo-vacina" class="muted" aria-live="polite"></p>' +
      situacoes(["APLICADA", "AGENDADA", "CANCELADA"]) +
      campo("fabricante", "Fabricante") +
      campo("numero_lote", "Número do lote") +
      seletor("via_aplicacao", "Via de aplicação", Object.entries(dados.nascimento.vias_vacina).map(([id, nome]) => ({ id, nome })), true) +
      campo("dose_etapa", "Dose / etapa", "text", true, 'maxlength="60"') +
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
      if (nome === "vacina") atualizarCatalogo();
      form.elements.situacao.dispatchEvent(new Event("change"));
      avisar(
        (nome === "consulta" ? "Consulta" : "Vacina") +
          " registrada. Abra a ficha do animal para conferir o histórico e a integração.",
      );
    });
  }
  const consulta = document.querySelector("#consulta");
  const vacina = document.querySelector("#vacina");
  const seletorVacina = vacina.elements.vacina_codigo;
  const tipoVacina = document.querySelector("#tipo-vacina");
  function mostrarTipo() {
    const selecionada = dados.vacinas.find((item) => item.codigo === seletorVacina.value);
    tipoVacina.textContent = selecionada ? "Tipo: " + selecionada.tipo : "";
  }
  function atualizarCatalogo() {
    const animal = dados.animais.find((item) => String(item.id) === vacina.elements.animal_id.value);
    const opcoes = animal ? dados.vacinas.filter((item) => item.especies.includes(animal.especie_id)) : [];
    const aviso = animal ? "Sem vacinas no catálogo para esta espécie" : "Selecione um animal";
    seletorVacina.replaceChildren(new Option(opcoes.length ? "Selecione a vacina" : aviso, ""));
    for (const item of opcoes) seletorVacina.add(new Option(item.nome, item.codigo));
    mostrarTipo();
  }
  vacina.elements.animal_id.onchange = atualizarCatalogo;
  seletorVacina.onchange = mostrarTipo;
  atualizarCatalogo();
  function exigirConsulta() {
    const realizada = consulta.elements.situacao.value === "REALIZADA";
    consulta.elements.peso_registrado_kg.required = realizada;
  }
  function exigirVacina() {
    const aplicada = vacina.elements.situacao.value === "APLICADA";
    for (const nome of [
      "fabricante",
      "numero_lote",
      "via_aplicacao",
      "validade_lote",
      "data_aplicacao",
    ]) {
      vacina.elements[nome].required = aplicada;
    }
    vacina.elements.data_agendada.required =
      vacina.elements.situacao.value === "AGENDADA";
  }
  consulta.elements.situacao.onchange = exigirConsulta;
  vacina.elements.situacao.onchange = exigirVacina;
  exigirConsulta();
  exigirVacina();
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
    const integracoes = await api("/clinica/integracoes?animal_id=" + id);
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
        '</section><section class="card"><h2>Integração governamental simulada</h2>' +
        '<button id="sincronizar">Sincronizar cadastro do animal</button>' +
        (integracoes.map((op) => '<article><p>' + escapar(op.tipo_operacao) + ' · ' +
          escapar(op.situacao) + ' · Tentativas: ' + op.quantidade_tentativas + '</p><p>Protocolo: ' +
          escapar(op.protocolo_externo || 'Aguardando confirmação') + '</p><p>' +
          escapar(op.mensagem_erro || '') + '</p>' + (op.situacao !== 'CONFIRMADA' ?
          '<button data-reenviar="' + op.id + '">Reenviar comunicação</button>' : '') + '</article>').join('') ||
          '<p>Nenhuma comunicação registrada.</p>') +
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
    document.querySelector("#sincronizar").onclick = async (event) => {
      event.currentTarget.disabled = true;
      try {
        await api("/clinica/animais/" + id + "/sincronizar", "POST");
        await ficha(id);
      } catch (erro) {
        avisar(erro.message, true);
        document.querySelector("#sincronizar").disabled = false;
      }
    };
    document.querySelectorAll("[data-reenviar]").forEach((button) => {
      button.onclick = async () => {
        button.disabled = true;
        try {
          await api("/clinica/integracoes/" + button.dataset.reenviar + "/reenviar", "POST");
          await ficha(id);
        } catch (erro) {
          avisar(erro.message, true);
          button.disabled = false;
        }
      };
    });
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
function acessoPublico(titulo, formulario) {
  app.innerHTML =
    '<div class="container"><section class="card login"><h1>' + titulo +
    '</h1><div id="aviso" role="status" tabindex="-1"></div>' + formulario +
    '<p><button type="button" class="secondary" id="voltar-login">Voltar ao login</button></p></section></div>';
  document.querySelector("#voltar-login").onclick = () => {
    history.replaceState(null, "", location.pathname + location.search);
    if (token) navegar("inicio");
    else login();
  };
}

function recuperarSenha() {
  acessoPublico(
    "Recuperar senha",
    '<form id="recuperar">' +
      campo("email", "E-mail", "email", true, 'autocomplete="email" maxlength="254"') +
      '<button type="submit">Solicitar link</button></form>',
  );
  enviarFormulario("recuperar", async (d, form) => {
    await api("/recuperacao-senha", "POST", d);
    form.reset();
    avisar("Se houver uma conta ativa e confirmada, enviaremos um link ao e-mail informado.");
  });
}

function definirSenha(acao, codigo) {
  const convite = acao === "convite";
  const atributos = 'autocomplete="new-password" minlength="12" maxlength="256"';
  acessoPublico(
    convite ? "Primeiro acesso" : "Redefinir senha",
    '<p>Use pelo menos 12 caracteres.</p><form id="definir-senha">' +
      campo("senha", "Nova senha", "password", true, atributos) +
      campo("confirmacao", "Confirme a nova senha", "password", true, atributos) +
      '<button type="submit">Definir senha</button></form>',
  );
  enviarFormulario("definir-senha", async (_dados, form) => {
    const senha = form.elements.senha.value;
    if (senha !== form.elements.confirmacao.value) throw new Error("As senhas devem ser iguais.");
    await api(convite ? "/convites/aceitar" : "/recuperacao-senha/concluir", "POST", { codigo, senha });
    history.replaceState(null, "", location.pathname + location.search);
    token = null;
    sessionStorage.removeItem("clinica_token");
    login("Senha definida. Entre com seu e-mail e a nova senha.");
  });
}

async function acessos() {
  const contas = await api("/veterinarios/acessos");
  estrutura(
    "Acessos da equipe",
    '<section class="card"><h2>Convidar veterinário</h2><form id="convite"><div class="grid">' +
      campo("nome_completo", "Nome completo", "text", true, 'maxlength="150"') +
      campo("cpf", "CPF", "text", true, 'inputmode="numeric" maxlength="14"') +
      campo("email", "E-mail profissional", "email", true, 'maxlength="254"') +
      campo("telefone", "Telefone (opcional)", "tel", false, 'maxlength="20"') +
      campo("numero_crmv", "Número do CRMV", "text", true, 'maxlength="20"') +
      seletor("uf_crmv", "UF do CRMV", dados.regrasAcesso.ufs.map((uf) => ({ id: uf, nome: uf }))) +
      '</div><button type="submit">Enviar convite</button></form></section>' +
      '<section class="card"><h2>Contas da clínica</h2>' +
      contas.map((conta) => {
        const ativa = conta.situacao === "ATIVO";
        const status = !ativa ? "Inativa" : conta.senha_confirmada ? "Ativa" : "Convite pendente";
        return '<div class="row item"><div><strong>' + escapar(conta.nome_completo) +
          '</strong><small>' + escapar(conta.email) + ' · ' +
          (conta.administrador ? "Gestor" : "Veterinário") + ' · ' + status +
          '</small></div><div>' +
          (ativa && !conta.senha_confirmada ?
            '<button class="secondary" data-reenviar="' + conta.id + '">Reenviar convite</button> ' : "") +
          (ativa && !conta.propria_conta ?
            '<button class="secondary" data-inativar="' + conta.id + '">Inativar conta</button>' : "") +
          '</div></div>';
      }).join("") + '</section>',
  );
  enviarFormulario("convite", async (d) => {
    d.uf_crmv = d.uf_crmv.toUpperCase();
    try {
      await api("/veterinarios/convites", "POST", d);
    } catch (erro) {
      if (erro.status === 503) await acessos();
      throw erro;
    }
    await acessos();
    avisar("Convite registrado. Confira o e-mail ou o terminal da API no modo de demonstração.");
  });
  document.querySelectorAll("[data-reenviar], [data-inativar]").forEach((botao) => {
    botao.onclick = async () => {
      const reenviar = botao.dataset.reenviar;
      if (!reenviar && !window.confirm("Inativar a conta e encerrar as sessões abertas?")) return;
      botao.disabled = true;
      try {
        if (reenviar) await api("/veterinarios/" + reenviar + "/reenviar-convite", "POST");
        else await api("/veterinarios/" + botao.dataset.inativar, "DELETE");
        await acessos();
        avisar(reenviar ? "Novo convite registrado." : "Conta inativada.");
      } catch (erro) {
        avisar(erro.message, true);
      } finally {
        botao.disabled = false;
      }
    };
  });
}

function abrirPagina() {
  const parametros = new URLSearchParams(location.hash.slice(1));
  const acao = parametros.get("acao");
  const codigo = parametros.get("codigo");
  if (codigo && (acao === "convite" || acao === "recuperacao")) definirSenha(acao, codigo);
  else if (token) navegar("inicio");
  else login();
}
window.addEventListener("hashchange", abrirPagina);
abrirPagina();

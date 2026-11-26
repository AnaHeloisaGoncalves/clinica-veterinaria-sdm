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
  if (tipo === "password") {
    return (
      '<div class="campo-senha"><label>' + titulo + '<input name="' + nome + '" type="password" ' +
      (obrigatorio ? "required " : "") + extra + '></label>' +
      '<button type="button" class="secondary alternar-senha" aria-pressed="false">Mostrar senha</button></div>'
    );
  }
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
      ["veterinarios", "Veterinários"],
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
    '<button type="submit">Entrar</button></form>' +
    '<p class="muted">Primeiro acesso? <button type="button" class="secondary" id="abrir-cadastro">Criar minha conta de veterinário</button></p></section></div>';
  document.querySelector("#abrir-cadastro").onclick = cadastrarVeterinario;
  enviarFormulario("login", async (d) => {
    const sessao = await api("/login", "POST", d);
    token = sessao.token_acesso;
    sessionStorage.setItem("clinica_token", token);
    await navegar("inicio");
  });
}
function cadastrarVeterinario() {
  app.innerHTML = '<div class="container"><section class="card login"><p class="muted">Clínica Veterinária</p><h1>Criar conta de veterinário</h1><div id="aviso" role="status" tabindex="-1"></div><form id="cadastro-veterinario">' +
    campo("nome_completo", "Nome completo", "text", true) + campo("cpf", "CPF", "text", true) +
    campo("email", "E-mail", "email", true) + campo("telefone", "Telefone") +
    campo("numero_crmv", "Número do CRMV", "text", true) + campo("uf_crmv", "UF do CRMV", "text", true, 'maxlength="2"') +
    campo("senha", "Senha (mínimo de 12 caracteres)", "password", true, 'minlength="12" autocomplete="new-password"') +
    '<button type="submit">Criar conta</button></form><button type="button" class="secondary" id="voltar-login">Voltar para o login</button></section></div>';
  document.querySelector("#voltar-login").onclick = () => login();
  enviarFormulario("cadastro-veterinario", async (dados) => {
    const resposta = await api("/cadastro-veterinario", "POST", dados);
    login(resposta.mensagem || "Conta criada com sucesso. Entre com seu e-mail e senha.");
  });
}

document.addEventListener("click", (evento) => {
  const botao = evento.target.closest(".alternar-senha");
  if (!botao) return;
  const entrada = botao.parentElement.querySelector('input[type="password"], input[type="text"]');
  const mostrar = entrada.type === "password";
  entrada.type = mostrar ? "text" : "password";
  botao.textContent = mostrar ? "Ocultar senha" : "Mostrar senha";
  botao.setAttribute("aria-pressed", String(mostrar));
});
async function navegar(pagina) {
  if (!token) return login();
  estrutura("Carregando", "<p>Aguarde...</p>");
  try {
    const entidades = ["tutores", "animais", "especies", "racas"];
    const listas = await Promise.all(entidades.map((e) => api("/" + e)));
    entidades.forEach((e, i) => (dados[e] = listas[i]));
    if (token) await ({ inicio, tutores, animais, clinica, catalogos, veterinarios })[pagina]();
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
function tutores(tutorEdicao = null, enderecoEdicao = null) {
  const editando = tutorEdicao !== null;
  estrutura(
    "Tutores",
    '<section class="card"><h2>' + (editando ? 'Editar tutor' : 'Novo tutor') + '</h2><form id="tutor"><div class="grid">' +
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
      '</div></fieldset><button type="submit">' + (editando ? 'Salvar tutor' : 'Cadastrar tutor') + '</button>' +
      (editando ? '<button type="button" id="cancelar-tutor">Cancelar edição</button>' : '') + '</form></section>' +
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
            '</p><p>CPF: ' + escapar(t.cpf) + ' · Cadastro: ' + escapar(t.cadastrado_em || '') + '</p>' +
            '<button data-editar-tutor="' + t.id + '">Consultar / editar ' + escapar(t.nome_completo) + '</button>' +
            (t.situacao === 'ATIVO' ? '<button data-inativar-tutor="' + t.id + '" class="secondary">Inativar tutor</button>' : ''),
        )
        .join("") || "<p>Nenhum tutor cadastrado.</p>") +
      "</section>",
  );
  const form = document.querySelector("#tutor");
  if (editando) {
    const valores = { ...tutorEdicao, ...enderecoEdicao };
    for (const campo of form.elements) if (campo.name) campo.value = valores[campo.name] ?? "";
    document.querySelector("#cancelar-tutor").onclick = () => tutores();
  }
  document.querySelectorAll("[data-editar-tutor]").forEach((b) => {
    b.onclick = async () => {
      try {
        const tutor = dados.tutores.find((t) => t.id == b.dataset.editarTutor);
        const endereco = await api("/enderecos/" + tutor.endereco_id);
        tutores(tutor, endereco);
      } catch (erro) { avisar(erro.message, true); }
    };
  });
  document.querySelectorAll("[data-inativar-tutor]").forEach((b) => {
    b.onclick = () => inativarRegistro("tutores", b.dataset.inativarTutor, "tutores");
  });
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
  form.elements.cep.addEventListener("change", () => document.querySelector("#buscar-cep").click());
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
    await api(editando ? "/clinica/tutores/" + tutorEdicao.id : "/clinica/tutores", editando ? "PUT" : "POST", { ...d, endereco });
    await navegar("tutores");
    avisar(editando ? "Tutor atualizado com sucesso." : "Tutor cadastrado com sucesso.");
  });
}
function animais(animalEdicao = null) {
  const editando = animalEdicao !== null;
  const opcoesEdicao = (lista, id) =>
    lista.filter((item) => ativos([item]).length || item.id == id);
  estrutura(
    "Animais",
    '<section class="card"><h2>' + (editando ? 'Editar animal' : 'Novo animal') + '</h2><form id="animal"><div class="grid">' +
      campo("nome", "Nome", "text", true) +
      (editando ? '' : campo("codigo_rfid", "Código RFID", "text", true, 'maxlength="48"')) +
      seletor("tutor_id", "Tutor", opcoesEdicao(dados.tutores, animalEdicao?.tutor_id)) +
      seletor("especie_id", "Espécie", opcoesEdicao(dados.especies, animalEdicao?.especie_id)) +
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
      '</div><p class="muted">Informe o nascimento ou a idade estimada. ' +
      (editando ? 'O RFID e os históricos serão preservados.' : 'O RFID precisa ser único.') +
      '</p><button type="submit">' + (editando ? 'Salvar alterações' : 'Cadastrar animal') +
      '</button>' + (editando ? '<button type="button" id="cancelar-edicao" class="secondary">Cancelar edição</button>' : '') + '</form></section>' +
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
            '</button><button data-editar-animal="' + a.id +
            '" class="secondary">Editar ' + escapar(a.nome) + '</button>' +
            (a.situacao === 'ATIVO' ? '<button data-inativar-animal="' + a.id + '" class="secondary">Inativar animal</button>' : '') + '</div>',
        )
        .join("") || "<p>Nenhum animal cadastrado.</p>") +
      "</section>",
  );
  const form = document.querySelector("#animal");
  form.elements.especie_id.onchange = () => {
    const racas = opcoesEdicao(dados.racas, animalEdicao?.raca_id).filter(
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
  if (editando) {
    for (const campo of form.elements) {
      if (campo.name && campo.name !== "raca_id")
        campo.value = animalEdicao[campo.name] ?? "";
    }
    form.elements.especie_id.onchange();
    form.elements.raca_id.value = animalEdicao.raca_id ?? "";
    document.querySelector("#cancelar-edicao").onclick = () => animais();
    form.elements.nome.focus();
  }
  enviarFormulario("animal", async (d) => {
    if (d.data_nascimento === null && d.idade_estimada_meses === null)
      throw new Error("Informe o nascimento ou a idade estimada.");
    await api(editando ? "/animais/" + animalEdicao.id : "/animais", editando ? "PUT" : "POST", d);
    await navegar("animais");
    avisar(editando ? "Dados do animal atualizados com sucesso." : "Animal cadastrado e RFID vinculado.");
  });
  document.querySelectorAll("[data-editar-animal]").forEach((b) => {
    b.onclick = () => animais(dados.animais.find((a) => a.id == b.dataset.editarAnimal));
  });
  document.querySelectorAll("[data-inativar-animal]").forEach((b) => {
    b.onclick = () => inativarRegistro("animais", b.dataset.inativarAnimal, "animais");
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
      campo("nome_vacina", "Nome da vacina", "text", true) +
      campo("tipo_vacina", "Tipo da vacina") +
      '<label class="checkbox"><input type="checkbox" name="antirrabica"> Vacina antirrábica</label>' +
      situacoes(["APLICADA", "AGENDADA", "CANCELADA"]) +
      campo("fabricante", "Fabricante") +
      campo("numero_lote", "Número do lote") +
      campo("via_aplicacao", "Via de aplicação") +
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
      form.elements.situacao.dispatchEvent(new Event("change"));
      avisar(
        (nome === "consulta" ? "Consulta" : "Vacina") +
          " registrada. Abra a ficha do animal para conferir o histórico e a integração.",
      );
    });
  }
  const consulta = document.querySelector("#consulta");
  const vacina = document.querySelector("#vacina");
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
          id: "Identificador interno",
          nome: "Nome",
          situacao: "Situação",
          sexo: "Sexo",
          cor: "Cor",
          peso_atual_kg: "Peso (kg)",
          data_nascimento: "Nascimento",
          idade_estimada_meses: "Idade estimada (meses)",
        }) +
        '<p>Tutor: ' + escapar(dados.tutores.find((t) => t.id == animal.tutor_id)?.nome_completo) +
        ' · Espécie: ' + escapar(dados.especies.find((e) => e.id == animal.especie_id)?.nome) +
        ' · Raça: ' + escapar(dados.racas.find((r) => r.id == animal.raca_id)?.nome || 'Não informada') + '</p>' +
        '</section>' + telaMicrochips(h, animal) + '<section class="card"><h2>Integração governamental simulada</h2>' +
        '<button id="sincronizar">Sincronizar cadastro do animal</button>' +
        (integracoes.map((op) => '<article><p>' + escapar(op.tipo_operacao) + ' · ' +
          escapar(op.situacao) + ' · Tentativas: ' + op.quantidade_tentativas + '</p><p>Protocolo: ' +
          escapar(op.protocolo_externo || 'Aguardando confirmação') + '</p><p>' +
          escapar(op.mensagem_erro || '') + '</p>' + detalhes(op, {
            id: 'ID da integração', vacina_id: 'Aplicação de vacina', chave_idempotencia: 'Chave de idempotência',
            solicitada_em: 'Solicitada em', respondida_em: 'Respondida em',
          }) + (op.situacao !== 'CONFIRMADA' ?
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
    if (document.querySelector("#substituir-microchip")) enviarFormulario("substituir-microchip", async (d) => {
      if (!confirm("Substituir o microchip? O vínculo anterior ficará no histórico.")) return;
      await api("/clinica/animais/" + id + "/microchip", "POST", d);
      await ficha(id);
      avisar("Novo microchip vinculado. Histórico anterior preservado. Sincronize o novo cadastro quando necessário.");
    });
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
      dados.especies.map((e) => "<article><h3>" + escapar(e.nome) + "</h3>" + botoesCatalogo('especies', e) + '</article>').join("") +
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
            "</p>" + botoesCatalogo('racas', r),
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
  document.querySelectorAll('[data-editar-catalogo]').forEach((b) => {
    b.onclick = () => editarCatalogo(b.dataset.editarCatalogo, b.dataset.id);
  });
  document.querySelectorAll('[data-inativar-catalogo]').forEach((b) => {
    b.onclick = () => inativarRegistro(b.dataset.inativarCatalogo, b.dataset.id, 'catalogos');
  });
}
if (token) navegar("inicio");
else login();

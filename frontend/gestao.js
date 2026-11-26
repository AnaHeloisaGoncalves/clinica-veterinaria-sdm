// Manutenção de cadastros e rastreabilidade. A autorização permanece na API.
async function inativarRegistro(entidade, id, pagina) {
  if (!confirm("Inativar este cadastro? Os registros e históricos serão preservados.")) return;
  try {
    await api("/" + entidade + "/" + id, "DELETE");
    await navegar(pagina);
    avisar("Cadastro inativado.");
  } catch (erro) { avisar(erro.message, true); }
}

function telaMicrochips(historico, animal) {
  return '<section class="card"><h2>Vínculos de microchip</h2>' +
    (historico.vinculos_microchip || []).map((m) => '<article><h3>' + escapar(m.codigo_rfid) +
      ' · ' + (m.encerrado_em ? 'Encerrado' : 'Vigente') + '</h3>' + detalhes(m, {
        vinculado_em: 'Data do vínculo', encerrado_em: 'Encerrado em',
        veterinario_nome: 'Veterinário responsável', veterinario_id: 'ID do profissional',
      }) + '</article>').join('') +
    (animal.situacao === 'ATIVO' ? '<form id="substituir-microchip"><h3>Substituir microchip</h3>' +
      campo('codigo_rfid', 'Novo código RFID', 'text', true, 'maxlength="48"') +
      '<button type="submit">Vincular novo microchip</button></form>' : '') + '</section>';
}

async function veterinarios(edicao = null) {
  const perfil = await api('/me');
  const lista = await api('/veterinarios');
  const admin = Boolean(perfil.administrador);
  estrutura('Veterinários', (admin ? '<section class="card"><h2>' +
    (edicao ? 'Editar profissional' : 'Novo profissional') + '</h2><form id="veterinario"><div class="grid">' +
    campo('nome_completo', 'Nome completo', 'text', true) +
    campo('cpf', 'CPF', 'text', true) + campo('email', 'E-mail', 'email', true) +
    campo('telefone', 'Telefone') + campo('numero_crmv', 'CRMV', 'text', true) +
    campo('uf_crmv', 'UF do CRMV', 'text', true, 'maxlength="2"') +
    (edicao ? '' : campo('senha', 'Senha inicial', 'password', true, 'minlength="12" maxlength="256" autocomplete="new-password"')) +
    '</div><p>Novas contas precisam confirmar a senha. Alterar o e-mail exige nova confirmação. O código é enviado ao log como e-mail simulado.</p>' +
    '<button type="submit">Salvar profissional</button>' +
    (edicao ? '<button type="button" id="cancelar-vet">Cancelar edição</button>' : '') + '</form></section>' :
    '<p>A manutenção de profissionais é restrita aos administradores.</p>') +
    '<section class="card"><h2>Profissionais cadastrados</h2>' + lista.map((v) =>
      '<article><h3>' + escapar(v.nome_completo) + '</h3>' + detalhes(v, {
        id: 'ID', cpf: 'CPF', email: 'E-mail', telefone: 'Telefone', numero_crmv: 'CRMV', uf_crmv: 'UF do CRMV',
        situacao: 'Situação', cadastrado_em: 'Cadastrado em', senha_confirmada_em: 'Senha confirmada em', ultimo_acesso_em: 'Último acesso',
      }) + '<p>Senha confirmada: ' + (v.senha_confirmada ? 'Sim' : 'Não') + '</p>' +
      (admin ? '<button data-editar-vet="' + v.id + '">Editar profissional</button>' +
        (v.situacao === 'ATIVO' ? '<button data-inativar-vet="' + v.id + '">Inativar profissional</button>' : '') +
        (!v.senha_confirmada && v.situacao === 'ATIVO' ? '<button data-confirmar-vet="' + v.id + '">Reenviar código</button>' : '') : '') +
      '</article>').join('') + '</section>');
  if (!admin) return;
  const form = document.querySelector('#veterinario');
  if (edicao) {
    for (const campo of form.elements) if (campo.name) campo.value = edicao[campo.name] ?? '';
    document.querySelector('#cancelar-vet').onclick = () => navegar('veterinarios');
  }
  enviarFormulario('veterinario', async (d) => {
    d.uf_crmv = d.uf_crmv.toUpperCase();
    await api('/veterinarios' + (edicao ? '/' + edicao.id : ''), edicao ? 'PUT' : 'POST', d);
    await navegar('veterinarios');
    avisar('Profissional salvo. Se houver confirmação pendente, consulte o código no e-mail simulado (log da clínica).');
  });
  document.querySelectorAll('[data-editar-vet]').forEach((b) => {
    b.onclick = async () => {
      try { await veterinarios(lista.find((v) => v.id == b.dataset.editarVet)); }
      catch (erro) { avisar(erro.message, true); }
    };
  });
  document.querySelectorAll('[data-inativar-vet]').forEach((b) => {
    b.onclick = () => inativarRegistro('veterinarios', b.dataset.inativarVet, 'veterinarios');
  });
  document.querySelectorAll('[data-confirmar-vet]').forEach((b) => {
    b.onclick = async () => {
      b.disabled = true;
      try {
        await api('/veterinarios/' + b.dataset.confirmarVet + '/reenviar-confirmacao', 'POST');
        avisar('Novo código gerado no e-mail simulado (log da clínica). Validade: uma hora.');
      } catch (erro) { avisar(erro.message, true); }
      finally { b.disabled = false; }
    };
  });
}

function botoesCatalogo(entidade, registro) {
  return '<p>' + escapar(registro.descricao || '') + ' · ' + escapar(registro.situacao) + '</p>' +
    '<button data-editar-catalogo="' + entidade + '" data-id="' + registro.id + '">Editar ' + escapar(registro.nome) + '</button>' +
    (!String(registro.situacao).startsWith('INATIV') ? '<button data-inativar-catalogo="' + entidade + '" data-id="' + registro.id + '">Inativar</button>' : '');
}

function editarCatalogo(entidade, id) {
  const registro = dados[entidade].find((r) => r.id == id);
  estrutura('Editar catálogo', '<section class="card"><form id="editar-catalogo">' +
    campo('nome', 'Nome', 'text', true, 'maxlength="80"') + texto('descricao', 'Descrição') +
    (entidade === 'racas' ? seletor('especie_id', 'Espécie', dados.especies.filter((e) =>
      !String(e.situacao).startsWith('INATIV') || e.id == registro.especie_id)) : '') +
    '<button type="submit">Salvar catálogo</button><button type="button" id="cancelar-catalogo">Cancelar</button></form></section>');
  for (const campo of document.querySelector('#editar-catalogo').elements)
    if (campo.name) campo.value = registro[campo.name] ?? '';
  document.querySelector('#cancelar-catalogo').onclick = () => catalogos();
  enviarFormulario('editar-catalogo', async (d) => {
    await api('/' + entidade + '/' + id, 'PUT', d);
    await navegar('catalogos');
    avisar('Catálogo atualizado.');
  });
}

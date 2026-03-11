from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Produto, Venda, ItemVenda
from datetime import datetime, timedelta
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')
vendas_bp = Blueprint('vendas', __name__, url_prefix='/vendas')


# ──────────────────────────── AUTH ────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_senha(senha):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Email ou senha incorretos.', 'danger')
    return render_template('login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        nome_loja = request.form.get('nome_loja', '').strip()

        if not all([nome, email, senha, nome_loja]):
            flash('Preencha todos os campos.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('register.html')

        user = User(nome=nome, email=email, nome_loja=nome_loja)
        user.set_senha(senha)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# ──────────────────────────── DASHBOARD ────────────────────────────

@main_bp.route('/')
@login_required
def dashboard():
    hoje = datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)

    vendas_hoje = db.session.query(func.coalesce(func.sum(Venda.total), 0)).filter(
        Venda.user_id == current_user.id,
        func.date(Venda.criado_em) == hoje,
    ).scalar()

    vendas_mes = db.session.query(func.coalesce(func.sum(Venda.total), 0)).filter(
        Venda.user_id == current_user.id,
        func.date(Venda.criado_em) >= inicio_mes,
    ).scalar()

    total_produtos = Produto.query.filter_by(user_id=current_user.id).count()
    total_vendas = Venda.query.filter_by(user_id=current_user.id).count()

    # dados para gráfico dos últimos 7 dias
    labels = []
    valores = []
    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)
        labels.append(dia.strftime('%d/%m'))
        total_dia = db.session.query(func.coalesce(func.sum(Venda.total), 0)).filter(
            Venda.user_id == current_user.id,
            func.date(Venda.criado_em) == dia,
        ).scalar()
        valores.append(float(total_dia))

    produtos = Produto.query.filter_by(user_id=current_user.id).filter(Produto.estoque > 0).all()
    ultimas_vendas = Venda.query.filter_by(user_id=current_user.id).order_by(Venda.criado_em.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        vendas_hoje=vendas_hoje,
        vendas_mes=vendas_mes,
        total_produtos=total_produtos,
        total_vendas=total_vendas,
        labels=labels,
        valores=valores,
        produtos=produtos,
        ultimas_vendas=ultimas_vendas,
    )


# ──────────────────────────── PRODUTOS ────────────────────────────

@produtos_bp.route('/')
@login_required
def listar():
    produtos = Produto.query.filter_by(user_id=current_user.id).order_by(Produto.criado_em.desc()).all()
    return render_template('produtos.html', produtos=produtos)


@produtos_bp.route('/novo', methods=['POST'])
@login_required
def criar():
    nome = request.form.get('nome', '').strip()
    preco = request.form.get('preco', '0')
    estoque = request.form.get('estoque', '0')

    if not nome:
        flash('Nome do produto é obrigatório.', 'danger')
        return redirect(url_for('produtos.listar'))

    try:
        preco = float(preco)
        estoque = int(estoque)
    except ValueError:
        flash('Preço ou estoque inválido.', 'danger')
        return redirect(url_for('produtos.listar'))

    produto = Produto(nome=nome, preco=preco, estoque=estoque, user_id=current_user.id)
    db.session.add(produto)
    db.session.commit()
    flash('Produto cadastrado!', 'success')
    return redirect(url_for('produtos.listar'))


@produtos_bp.route('/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    produto = Produto.query.get_or_404(id)
    if produto.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('produtos.listar'))

    produto.nome = request.form.get('nome', produto.nome).strip()
    try:
        produto.preco = float(request.form.get('preco', produto.preco))
        produto.estoque = int(request.form.get('estoque', produto.estoque))
    except ValueError:
        flash('Valores inválidos.', 'danger')
        return redirect(url_for('produtos.listar'))

    db.session.commit()
    flash('Produto atualizado!', 'success')
    return redirect(url_for('produtos.listar'))


@produtos_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    produto = Produto.query.get_or_404(id)
    if produto.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('produtos.listar'))

    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído.', 'success')
    return redirect(url_for('produtos.listar'))


# ──────────────────────────── VENDAS ────────────────────────────

@vendas_bp.route('/')
@login_required
def listar():
    vendas = Venda.query.filter_by(user_id=current_user.id).order_by(Venda.criado_em.desc()).all()
    return render_template('vendas.html', vendas=vendas)


@vendas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if request.method == 'POST':
        produtos_ids = request.form.getlist('produto_id')
        quantidades = request.form.getlist('quantidade')
        forma_pagamento = request.form.get('forma_pagamento', 'dinheiro')

        formas_validas = ('dinheiro', 'pix', 'credito', 'debito')
        if forma_pagamento not in formas_validas:
            forma_pagamento = 'dinheiro'

        if not produtos_ids:
            flash('Adicione pelo menos um produto.', 'danger')
            return redirect(url_for('vendas.nova'))

        venda = Venda(user_id=current_user.id, total=0, forma_pagamento=forma_pagamento)
        db.session.add(venda)
        db.session.flush()

        total = 0
        for pid, qtd in zip(produtos_ids, quantidades):
            try:
                pid = int(pid)
                qtd = int(qtd)
            except ValueError:
                continue

            produto = Produto.query.get(pid)
            if not produto or produto.user_id != current_user.id or qtd <= 0:
                continue

            if produto.estoque < qtd:
                flash(f'Estoque insuficiente para {produto.nome}.', 'danger')
                db.session.rollback()
                return redirect(url_for('vendas.nova'))

            subtotal = produto.preco * qtd
            item = ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=qtd,
                preco_unitario=produto.preco,
                subtotal=subtotal,
            )
            db.session.add(item)
            produto.estoque -= qtd
            total += subtotal

        venda.total = total
        db.session.commit()
        flash(f'Venda registrada! Total: R$ {total:.2f}', 'success')
        return redirect(url_for('vendas.listar'))

    produtos = Produto.query.filter_by(user_id=current_user.id).filter(Produto.estoque > 0).all()
    return render_template('nova_venda.html', produtos=produtos)


@vendas_bp.route('/<int:id>')
@login_required
def detalhe(id):
    venda = Venda.query.get_or_404(id)
    if venda.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('vendas.listar'))
    return render_template('detalhe_venda.html', venda=venda)

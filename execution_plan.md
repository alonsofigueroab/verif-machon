# Plan de Ejecución Técnica: Modificación de Masa Sísmica, Volumen Subterráneo y Extensión de Aberturas en Machón

## Resumen de Objetivos
Modificar la lógica de cálculo en el notebook Marimo (`verif-machon.py`) para:
1. **Separación de Masa Sísmica ($W_{\text{sup}}$) y Masa Total ($W_{\text{total}}$)**:
   - **Masa Sísmica ($W_{\text{sup}}$)**: La determinación de las cargas sísmicas ($F_{\text{sismo}} = C_s \cdot W_{\text{sup}}$) considera únicamente la masa del machón ubicada por sobre el nivel del terreno ($H_{\text{sup}} = H - D_{\text{emb}}$).
   - **Fuerza Resistente y Volcamiento ($W_{\text{total}}$)**: El cálculo de la resistencia al deslizamiento ($\mu \cdot W_{\text{total}} + P_p$) y el momento resistente al volcamiento ($M_r = W_{\text{total}} \cdot L / 2$) se mantiene considerando la masa total del machón ($V_{\text{net}}$).
2. **Extensión de Aberturas sobre Nivel de Terreno ($2r$)**:
   - La abertura (o zona de paso de cañerías) se extienda verticalmente una altura de **$2 \cdot r$ por sobre el nivel del terreno** ($D_{\text{emb}}$).
   - La porción de área neta sobre el terreno ($A_{\text{net,sup}}$) descuenta la proyección de la abertura que se extiende $2 \cdot r$ por encima de la cota $D_{\text{emb}}$, ajustando la masa aérea $W_{\text{sup}}$ y su centroide $z_{\text{cg,sup}}$.

---

## Fase 1: Comandos de Entorno y Preparación (PowerShell / `uv`)

Ejecutar los siguientes comandos en PowerShell desde la raíz del repositorio:

```powershell
# 1. Asegurar dependencias del proyecto mediante uv
uv add marimo matplotlib numpy

# 2. Comprobar sintaxis previa de verif-machon.py
uv run python -m py_compile verif-machon.py

# 3. Lanzar servidor Marimo en el puerto 2137
uv run marimo edit verif-machon.py --port 2137
```

---

## Fase 2: Plan de Modificaciones Modulares en `verif-machon.py`

### 1. Parámetros de Entrada de Empotramiento (`D_emb_input`)
Garantizar que $D_{\text{emb}}$ defina el nivel de terreno para el volumen bajo tierra y la referencia de extensión de la abertura.

**Bloque Modular de Código:**
```python
@app.cell
def _(mo):
    pp_toggle_input = mo.ui.switch(
        value=False,
        label="Incluir presión pasiva del terreno",
    )
    D_emb_input = mo.ui.number(
        value=0.5, start=0.0, stop=5.0, step=0.05,
        label="Profundidad bajo terreno D_emb (m)",
    )
    gamma_suelo_input = mo.ui.number(
        value=18.0, start=12.0, stop=22.0, step=0.5,
        label="Peso unitario del suelo γ_suelo (kN/m³)",
    )
    factor_mov_input = mo.ui.number(
        value=0.5, start=0.1, stop=1.0, step=0.05,
        label="Factor de movilización de Pp (1.0 = Rankine completo)",
    )
    mo.vstack([
        mo.hstack([D_emb_input, pp_toggle_input]),
        mo.hstack([gamma_suelo_input, factor_mov_input]),
    ])
    return D_emb_input, factor_mov_input, gamma_suelo_input, pp_toggle_input
```

---

### 2. Modificación de la Celda de Geometría (`## 2. Geometría`)
Ajustar el cálculo del volumen y área neta incorporando la condición de que la abertura penetra / se extiende $2 \cdot r$ por sobre el nivel de terreno.

**Bloque Modular de Código:**
```python
@app.cell
def _(
    B_input,
    D_emb_input,
    H_input,
    L_input,
    ancho_abertura_input,
    math,
    n_pipes_input,
    sep_input,
):
    L = L_input.value
    H = H_input.value
    B = B_input.value
    D_emb = min(D_emb_input.value, H)
    sep = sep_input.value
    n_pipes = int(n_pipes_input.value)

    r = ancho_abertura_input.value / 2.0

    # Geometría base de abertura
    A_rect = 2.0 * r * r
    A_semi = math.pi * r ** 2 / 2.0
    A_ab_base = A_semi + A_rect
    
    # Altura total de la abertura considerando la extensión de 2*r sobre el nivel de terreno:
    # La abertura abarca la zona enterrada D_emb + una extensión vertical de 2*r sobre el terreno.
    h_ext_sup = 2.0 * r  # Extensión sobre terreno = 2 * radio cañería
    h_ab_total = min(H, D_emb + h_ext_sup)

    z_rect = r / 2.0
    z_semi = r + (4.0 * r) / (3.0 * math.pi)
    z_ab = (A_rect * z_rect + A_semi * z_semi) / A_ab_base

    if n_pipes == 1:
        centros = [L / 2.0]
    else:
        centros = [L / 2.0 - sep / 2.0, L / 2.0 + sep / 2.0]

    warnings = []
    if h_ab_total > H:
        warnings.append(
            f"⚠️ La altura total de abertura ({h_ab_total:.3f} m) supera la altura H ({H:.3f} m)."
        )
    for xc in centros:
        if xc - r < 0 or xc + r > L:
            warnings.append(
                "⚠️ Alguna abertura excede los límites del machón en la dirección L."
            )
            break
    if n_pipes == 2 and (centros[0] + r > centros[1] - r):
        warnings.append("⚠️ Las dos aberturas se traslapan entre sí (revisar separación).")

    # 1. GEOMETRÍA TOTAL MACHÓN (para Resistencia al Deslizamiento y Volcamiento)
    A_gross = L * H
    A_ab_total = n_pipes * A_ab_base
    A_net = A_gross - A_ab_total
    z_gross = H / 2.0
    z_cg_net = (A_gross * z_gross - A_ab_total * z_ab) / A_net if A_net > 0 else 0.0
    V_net = A_net * B

    # 2. GEOMETRÍA SOBRE TERRENO (para Determinación de Cargas Sísmicas)
    H_sup = max(0.0, H - D_emb)
    A_gross_sup = L * H_sup

    # Área de abertura que queda sobre el nivel de terreno (extensión de 2*r sobre cota D_emb)
    # Ancho de la abertura = 2*r; Altura proyectada sobre terreno = min(H_sup, h_ext_sup) = min(H_sup, 2*r)
    h_sup_ab = min(H_sup, h_ext_sup)
    A_ab_sup = (2.0 * r) * h_sup_ab

    A_net_sup = max(0.0, A_gross_sup - n_pipes * A_ab_sup)
    V_net_sup = A_net_sup * B
    
    # Centroide de la masa aérea desde la base del machón (punto de aplicación del sismo)
    z_cg_sup = D_emb + (H_sup / 2.0) if H_sup > 0 else z_cg_net

    return (
        A_ab_base,
        A_net,
        A_net_sup,
        B,
        D_emb,
        H,
        H_sup,
        L,
        V_net,
        V_net_sup,
        centros,
        h_ab_total,
        h_ext_sup,
        n_pipes,
        r,
        warnings,
        z_cg_net,
        z_cg_sup,
    )
```

---

### 3. Ajuste de Determinación de Cargas (`## 3. Cargas`)
El peso $W_{\text{sup}} = \gamma_c \cdot V_{\text{net,sup}}$ determina la fuerza sísmica $F_{\text{sismo}} = C_s \cdot W_{\text{sup}}$ aplicada en $z_{\text{cg,sup}}$, mientras que el peso neto total $W = \gamma_c \cdot V_{\text{net}}$ representa la masa estabilizadora.

**Bloque Modular de Código:**
```python
@app.cell
def _(
    Cs_input,
    Q_tub_input,
    V_net,
    V_net_sup,
    gamma_c_input,
    mo,
    n_pipes,
    r_pipe_input,
    z_cg_net,
    z_cg_sup,
):
    g = 9.81
    gamma_c = gamma_c_input.value  # kg/m3
    gamma_c_kN = gamma_c * g / 1000.0  # kN/m3

    W = gamma_c_kN * V_net  # kN, peso neto TOTAL (deslizamiento y volcamiento)
    W_sup = gamma_c_kN * V_net_sup  # kN, peso neto SOBRE TERRENO (sismo)

    Cs = Cs_input.value
    F_sismo = Cs * W_sup  # kN, carga sísmica basada en la masa sobre terreno

    Q_tub = Q_tub_input.value  # kN, por cañería
    F_tub = n_pipes * Q_tub  # kN, total
    z_tub = r_pipe_input.value  # m, altura de aplicación

    mo.md(
        f"""
        | Carga | Valor | Punto de aplicación (altura desde la base) |
        |---|---|---|
        | Peso propio neto total W | {W:.2f} kN | z = {z_cg_net:.3f} m (centroide total) |
        | Peso sobre terreno W_sup | {W_sup:.2f} kN | z = {z_cg_sup:.3f} m (centroide masa aérea) |
        | Carga transversal total F_tub ({n_pipes} cañerías) | {F_tub:.2f} kN | z = {z_tub:.3f} m |
        | Carga sísmica F_sismo = Cs·W_sup | {F_sismo:.2f} kN | z = {z_cg_sup:.3f} m (centroide masa aérea) |
        """
    )
    return F_sismo, F_tub, W, W_sup, z_tub
```

---

### 4. Ajuste de Verificaciones E structurales (`## 4. Verificaciones`)
Garantizar que el momento resistente al volcamiento ($M_r = W_{\text{total}} \cdot L / 2$) y la resistencia por fricción al deslizamiento ($\mu \cdot W_{\text{total}} + P_p$) utilicen el peso total $W$.

**Bloque Modular de Código:**
```python
@app.cell
def _(
    A_base_net,
    B,
    D_emb,
    F_sismo,
    F_tub,
    I_base_net,
    L,
    W,
    factor_mov_input,
    gamma_suelo_input,
    math,
    mu,
    phi_input,
    pp_toggle_input,
    z_cg_sup,
    z_tub,
):
    # Volcamiento: F_sismo actúa en z_cg_sup
    M_ot_suma = F_tub * z_tub + F_sismo * z_cg_sup
    M_ot_resta = abs(F_tub * z_tub - F_sismo * z_cg_sup)
    M_ot = max(M_ot_suma, M_ot_resta)

    # Momento resistente (utiliza masa total W)
    M_r = W * (L / 2.0)

    FS_volc_suma = M_r / M_ot_suma if M_ot_suma > 0 else float("inf")
    FS_volc_resta = M_r / M_ot_resta if M_ot_resta > 0 else float("inf")
    FS_volc = min(FS_volc_suma, FS_volc_resta)

    # Deslizamiento (fuerza normal resistente utiliza masa total W)
    Pp_total = 0.0
    if pp_toggle_input.value and D_emb > 0:
        Kp = math.tan(math.radians(45.0 + phi_input.value / 2.0)) ** 2
        Pp_total = (
            factor_mov_input.value * 0.5 * Kp
            * gamma_suelo_input.value * D_emb ** 2 * B
        )

    H_suma = F_tub + F_sismo
    H_resta = abs(F_tub - F_sismo)

    FS_desl_suma = (mu * W + Pp_total) / H_suma if H_suma > 0 else float("inf")
    FS_desl_resta = (mu * W + Pp_total) / H_resta if H_resta > 0 else float("inf")
    FS_desl = min(FS_desl_suma, FS_desl_resta)

    # Presión de contacto sobre suelo
    e = M_ot / W if W > 0 else 0.0
    q_max = W / A_base_net + M_ot * (L / 2.0) / I_base_net
    q_min = W / A_base_net - M_ot * (L / 2.0) / I_base_net
    contacto_total = q_min >= 0

    return (
        FS_desl,
        FS_desl_resta,
        FS_desl_suma,
        FS_volc,
        FS_volc_resta,
        FS_volc_suma,
        M_ot,
        Pp_total,
        contacto_total,
        e,
        q_max,
        q_min,
    )
```

---

### 5. Actualización de la Función Auxiliar de Sensibilidad (`calc_fsd`)

**Bloque Modular de Código:**
```python
@app.cell
def _(math):
    def calc_fsd(
        L, H, B, r, sep, n_pipes, Q_tub, Cs, gamma_c, mu,
        pp_enabled=False, D_emb=0.0, gamma_suelo=18.0, phi_deg=32.0, factor_mov=1.0,
    ):
        A_rect = 2.0 * r * r
        A_semi = math.pi * r ** 2 / 2.0
        A_ab_base = A_semi + A_rect
        A_gross = L * H
        A_net = A_gross - n_pipes * A_ab_base
        if A_net <= 0:
            return float("nan")
        V_net = A_net * B
        
        # Extensión de abertura sobre terreno (2*r sobre cota D_emb)
        D_emb_eff = min(D_emb, H)
        H_sup = max(0.0, H - D_emb_eff)
        A_gross_sup = L * H_sup
        
        h_sup_ab = min(H_sup, 2.0 * r)
        A_ab_sup = (2.0 * r) * h_sup_ab
        A_net_sup = max(0.0, A_gross_sup - n_pipes * A_ab_sup)
        V_net_sup = A_net_sup * B

        gamma_c_kN = gamma_c * 9.81 / 1000.0
        W_total = gamma_c_kN * V_net
        W_sup = gamma_c_kN * V_net_sup

        F_sismo = Cs * W_sup
        F_tub = n_pipes * Q_tub
        H_suma = F_tub + F_sismo
        H_resta = abs(F_tub - F_sismo)
        H_total = max(H_suma, H_resta)

        Pp_total = 0.0
        if pp_enabled and D_emb_eff > 0:
            Kp = math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2
            Pp_total = factor_mov * 0.5 * Kp * gamma_suelo * D_emb_eff ** 2 * B

        if H_total <= 0:
            return float("inf")
        return (mu * W_total + Pp_total) / H_total

    return (calc_fsd,)
```

---

## Fase 3: Validación Post-Ejecución (PowerShell / `uv`)

```powershell
# 1. Verificación de compilación Python
uv run python -m py_compile verif-machon.py

# 2. Exportación de reporte estático para validar reactividad de Marimo
uv run marimo export html verif-machon.py -o build_test.html
```

import pandas as pd  # 新增的导入
import streamlit as st
import math

def calculate_equivalent_rate(fv, years):
    """计算养老金终值对应的等效年利率（二分法优化版）"""
    if years == 0 or fv <= 0:
        return 0.0

    pmt = 12000
    target = fv

    def annuity_fv(r):
        if r <= 1e-6:
            return pmt * years * (1 + r)
        return pmt * (1 + r) * (((1 + r)**years - 1) / r)

    low, high = 0.0, 0.3
    for _ in range(100):
        if annuity_fv(high) > target:
            break
        high *= 2

    epsilon = 1e-6
    for _ in range(1000):
        mid = (low + high) / 2
        current = annuity_fv(mid)
        if abs(current - target) < epsilon:
            return round(mid, 5)
        if current < target:
            low = mid
        else:
            high = mid

    return round((low + high)/2, 5)

def calculate_comparison(rate, years, tax_rate):
    """核心计算逻辑（仅在最后一年扣除养老金3%税）"""
    rate = rate / 100
    tax_rate = tax_rate / 100

    pension = 0
    tax_refund_invest = 0
    normal_save = 0

    yearly_data = []

    for year in range(1, years + 1):
        pension = (pension + 12000) * (1 + rate)
        tax_refund = 12000 * tax_rate
        tax_refund_invest = (tax_refund_invest + tax_refund) * (1 + rate)
        normal_save = (normal_save + 12000) * (1 + rate)

        total_invest = 12000 * year
        if year == years:
            current_a = pension * 0.97 + tax_refund_invest
        else:
            current_a = pension + tax_refund_invest
        current_b = normal_save

        rate_a = (current_a - total_invest) / total_invest * 100
        rate_b = (current_b - total_invest) / total_invest * 100

        yearly_data.append({
            "年份": f"第{year}年",  # 修改这里
            "养老金金额": int(round(current_a)),
            "存款金额": int(round(current_b)),
            "养老金收益": round(rate_a, 1),
            "存款收益": round(rate_b, 1)
        })

    final_a = yearly_data[-1]["养老金金额"]
    final_b = yearly_data[-1]["存款金额"]

    return {
        "方案A终值": final_a,
        "方案B终值": final_b,
        "收益差额": final_a - final_b,
        "每年数据": yearly_data,
        "参数": f"{rate*100}%利率/{years}年/{tax_rate*100}%退税"
    }

# 页面配置
st.set_page_config(page_title="养老金收益计算器", page_icon="💰", layout="wide")

# 侧边栏输入设置
with st.sidebar:
    st.header("计算参数设置")
    # 缴费年份（默认20年）
    years = st.number_input(
        "距退休缴纳年数",
        min_value=1,
        value=20,  # 新增默认值
        step=1,
        help="预计继续缴纳养老金的年数"
    )

    # 存款利率（默认1.9%）
    rate = st.number_input(
        "定存利率（%）",
        min_value=0.0,
        value=1.9,  # 新增默认值
        step=0.1,
        format="%.1f",
        help="银行定期存款或理财产品的预期年化收益率"
    )

    tax_rate = st.selectbox(
        "退税税率",
        options=[0, 3, 10, 20, 25, 30, 35, 45],
        format_func=lambda x: f"{x}%",
        index=1  # 默认选中3%
    )

# 主内容区域
st.title("💰 12000每年个人养老金VS定存收益计算器")

if st.sidebar.button("开始计算"):
    # 执行计算
    result = calculate_comparison(rate, years, tax_rate)
    equiv_rate = calculate_equivalent_rate(result['方案A终值'], years)

    # 显示最终结果
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 最终对比结果")
        final_table = [
            ["💵 终值金额", f"¥{result['方案A终值']:,.0f}", f"¥{result['方案B终值']:,.0f}"],
            ["📈 收益差额", f"¥{abs(result['收益差额']):,.0f} ({'养老金领先' if result['收益差额'] > 0 else '存款领先'})", ""],
            ["💹 实际年化率", f"{equiv_rate*100:.1f}%", f"{rate}%"],
            ["⚙️ 计算参数", result["参数"], ""]
        ]
        st.table(pd.DataFrame(final_table, columns=["对比项", "方案A（养老金）", "方案B（普通存款）"]))

    # 决策建议
    with col2:
        st.subheader("💡 决策建议")
        diff = result['收益差额']
        if diff > 0:
            st.success(f"""
            **✅ 推荐个人养老金方案**  
            • 累计多赚 ¥{diff:,.0f}  
            • 关键优势：{tax_rate}%退税税率 > 3%取出税率  
            • 注：退税收益已每年复利计算，3%税率仅影响最终取出金额
            """)
        elif diff < 0:
            st.success(f"""
            **✅ 推荐普通存款方案**  
            • 累计多赚 ¥{-diff:,.0f}  
            • 原因：退税税率 ≤ 取出税率导致收益倒挂
            """)
        else:
            st.info("两种方案收益完全相同")

    # 显示逐年数据
    st.subheader("📅 逐年增长详情(退休领取时缴税3%）")
    df = pd.DataFrame(result["每年数据"])
    df["养老金金额"] = df["养老金金额"].apply(lambda x: f"¥{x:,.0f}")
    df["存款金额"] = df["存款金额"].apply(lambda x: f"¥{x:,.0f}")
    df["养老金收益"] = df["养老金收益"].apply(lambda x: f"{x}%")
    df["存款收益"] = df["存款收益"].apply(lambda x: f"{x}%")

    st.dataframe(
        df[["年份", "养老金金额", "养老金收益", "存款金额", "存款收益"]],
        hide_index=True,
        use_container_width=True,
        height=(len(df) * 35 + 35)  # 自动调整表格高度
    )
# 注意事项
st.sidebar.markdown("---")
st.sidebar.info("""
**注意事项：**
1. 计算假设每年年初存入12000元
2. 养老金账户仅最后取出时扣除3%税率
3. 退税金额按年即时再投资
4. 计算结果仅供参考，不构成投资建议
""")
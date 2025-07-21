import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional

from utils.database import Database
from utils.logger import get_logger

class PerformanceAnalyzer:
    """性能分析器，用于分析告警的准确率和性能"""
    
    def __init__(self, db: Database):
        """初始化性能分析器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.logger = get_logger()
        self._output_path = None
        self._output_dir = None
    
    def analyze(self, days: int = 30, output_path: str = "performance_report.html") -> None:
        """分析告警性能并生成报告
        
        Args:
            days: 分析最近多少天的数据，默认30天
            output_path: 输出报告的路径
        """
        self.logger.info(f"开始分析最近{days}天的告警性能...")
        self._output_path = output_path
        self._output_dir = os.path.dirname(os.path.abspath(output_path))
        
        # 确保输出目录存在
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
            self.logger.info(f"创建输出目录: {self._output_dir}")
        
        try:
            # 获取性能摘要
            summary = self.db.get_performance_summary(days)
            self.logger.info(f"获取到性能摘要: 总告警数 {summary.get('total_alerts', 0)}")
            
            # 获取详细性能数据
            performance_data = self.db.get_alert_performance(days=days)
            
            if not performance_data:
                self.logger.warning(f"没有找到最近{days}天的告警性能数据")
                # 即使没有数据，也创建一个空的DataFrame和基本报告
                df = pd.DataFrame()
            else:
                self.logger.info(f"获取到 {len(performance_data)} 条告警性能数据")
                # 转换为DataFrame进行分析
                df = pd.DataFrame(performance_data)
            
            # 生成HTML报告
            self._generate_html_report(df, summary, output_path)
            
            self.logger.info(f"性能分析完成，报告已保存到 {output_path}")
        except Exception as e:
            self.logger.error(f"生成性能分析报告时出错: {e}")
            # 尝试生成一个基本的错误报告
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"""<html>
                    <head>
                        <title>加密货币告警性能分析报告 - 错误</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1, h2 {{ color: #333; }}
                            .error-box {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <h1>加密货币告警性能分析报告 - 错误</h1>
                        <p>生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <div class="error-box">
                            <h2>⚠️ 生成报告时出错</h2>
                            <p>在尝试生成性能分析报告时发生错误:</p>
                            <pre>{str(e)}</pre>
                            <p>可能的原因:</p>
                            <ul>
                                <li>数据库连接问题</li>
                                <li>数据库结构不匹配</li>
                                <li>数据格式不正确</li>
                            </ul>
                            <p>请检查日志文件获取更多信息。</p>
                        </div>
                    </body>
                    </html>""")
                self.logger.info(f"已生成错误报告: {output_path}")
            except Exception as write_err:
                self.logger.error(f"尝试生成错误报告时也失败: {write_err}")

    
    def _generate_html_report(self, df: pd.DataFrame, summary: Dict[str, Any], output_path: str) -> None:
        """生成HTML报告
        
        Args:
            df: 性能数据DataFrame
            summary: 性能摘要
            output_path: 输出报告的路径
        """
        # 创建HTML内容
        html_content = []
        
        # 添加标题
        html_content.append("""<html>
        <head>
            <title>加密货币告警性能分析报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .positive { color: green; }
                .negative { color: red; }
                .summary-box { background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .chart-container { margin-bottom: 30px; }
                .warning-box { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <h1>加密货币告警性能分析报告</h1>
            <p>生成时间: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</p>")
        
        # 检查是否有足够的数据
        has_data = not df.empty and 'profit_if_follow' in df.columns
        valid_data = df.dropna(subset=['profit_if_follow']) if has_data else pd.DataFrame()
        has_valid_data = not valid_data.empty if has_data else False
        
        if not has_valid_data:
            html_content.append("""<div class="warning-box">
                <h2>⚠️ 数据不足</h2>
                <p>没有足够的告警性能数据来生成完整的分析报告。可能的原因：</p>
                <ul>
                    <li>数据库中没有足够的告警记录</li>
                    <li>告警记录中缺少性能数据</li>
                    <li>数据库连接或查询出现问题</li>
                </ul>
                <p>建议：</p>
                <ul>
                    <li>确保数据库文件存在并且可访问</li>
                    <li>检查告警记录是否正确记录了性能数据</li>
                    <li>尝试增加分析的天数范围</li>
                </ul>
            </div>""")
        
        # 添加摘要信息
        html_content.append("""<div class="summary-box">
            <h2>性能摘要</h2>
            <table>
                <tr>
                    <th>指标</th>
                    <th>值</th>
                </tr>""")
        
        html_content.append(f"""<tr>
                    <td>总告警数</td>
                    <td>{summary.get('total_alerts', 0)}</td>
                </tr>""")
        
        html_content.append(f"""<tr>
                    <td>盈利告警数</td>
                    <td>{summary.get('profitable_alerts', 0)}</td>
                </tr>""")
        
        win_rate = summary.get('win_rate', 0)
        html_content.append(f"""<tr>
                    <td>胜率</td>
                    <td>{win_rate:.2f}%</td>
                </tr>""")
        
        avg_profit = summary.get('avg_profit', 0)
        html_content.append(f"""<tr>
                    <td>平均收益</td>
                    <td class="{'positive' if avg_profit >= 0 else 'negative'}">{avg_profit:.2f}%</td>
                </tr>""")
        
        max_profit = summary.get('max_profit', 0)
        html_content.append(f"""<tr>
                    <td>最大收益</td>
                    <td class="positive">{max_profit:.2f}%</td>
                </tr>""")
        
        max_loss = summary.get('max_loss', 0)
        html_content.append(f"""<tr>
                    <td>最大亏损</td>
                    <td class="negative">{max_loss:.2f}%</td>
                </tr>""")
        
        html_content.append("</table>")
        
        # 添加按方向的统计
        if 'by_direction' in summary and summary['by_direction']:
            html_content.append("""<h3>按方向统计</h3>
                <table>
                    <tr>
                        <th>方向</th>
                        <th>告警数</th>
                        <th>盈利数</th>
                        <th>胜率</th>
                        <th>平均收益</th>
                    </tr>""")
            
            for direction, stats in summary['by_direction'].items():
                html_content.append(f"""<tr>
                        <td>{direction}</td>
                        <td>{stats.get('total', 0)}</td>
                        <td>{stats.get('profitable', 0)}</td>
                        <td>{stats.get('win_rate', 0):.2f}%</td>
                        <td class="{'positive' if stats.get('avg_profit', 0) >= 0 else 'negative'}">{stats.get('avg_profit', 0):.2f}%</td>
                    </tr>""")
            
            html_content.append("</table>")
        
        html_content.append("</div>")
        
        # 生成图表
        if has_valid_data:
            self.logger.info(f"开始生成图表，有效数据点数量: {len(valid_data)}")
            # 按时间的收益率趋势图
            self._add_profit_trend_chart(valid_data, html_content)
            
            # 按交易对的性能对比图
            self._add_symbol_performance_chart(valid_data, html_content)
            
            # 按信号分数的性能对比图
            self._add_score_performance_chart(valid_data, html_content)
        else:
            html_content.append("""<div class="warning-box">
                <h3>⚠️ 无法生成图表</h3>
                <p>由于数据不足或无效，无法生成性能分析图表。</p>
            </div>""")
        
        # 添加详细数据表格
        html_content.append("""<h2>详细告警性能数据</h2>""")
        
        if not df.empty:
            html_content.append("""<table>
                <tr>
                    <th>时间</th>
                    <th>交易对</th>
                    <th>方向</th>
                    <th>分数</th>
                    <th>初始价格</th>
                    <th>1小时后</th>
                    <th>4小时后</th>
                    <th>24小时后</th>
                    <th>1小时变化</th>
                    <th>4小时变化</th>
                    <th>24小时变化</th>
                    <th>收益</th>
                </tr>""")
            
            for _, row in df.iterrows():
                # 格式化价格变化和收益，添加颜色，确保处理None值
                price_change_1h = 0 if row.get('price_change_1h') is None else row.get('price_change_1h', 0)
                price_change_4h = 0 if row.get('price_change_4h') is None else row.get('price_change_4h', 0)
                price_change_24h = 0 if row.get('price_change_24h') is None else row.get('price_change_24h', 0)
                profit = 0 if row.get('profit_if_follow') is None else row.get('profit_if_follow', 0)
                
                price_change_1h_class = "positive" if price_change_1h >= 0 else "negative"
                price_change_4h_class = "positive" if price_change_4h >= 0 else "negative"
                price_change_24h_class = "positive" if price_change_24h >= 0 else "negative"
                profit_class = "positive" if profit >= 0 else "negative"
                
                html_content.append(f"""<tr>
                    <td>{row.get('alert_time', '')}</td>
                    <td>{row.get('display_name', '')}</td>
                    <td>{row.get('direction', '')}</td>
                    <td>{row.get('score', '')}</td>
                    <td>{row.get('initial_price', ''):.4f}</td>
                    <td>{row.get('price_1h', '') if pd.notna(row.get('price_1h', '')) else '-'}</td>
                    <td>{row.get('price_4h', '') if pd.notna(row.get('price_4h', '')) else '-'}</td>
                    <td>{row.get('price_24h', '') if pd.notna(row.get('price_24h', '')) else '-'}</td>
                    <td class="{price_change_1h_class}">{f"{price_change_1h:.2f}%" if pd.notna(price_change_1h) else '-'}</td>
                    <td class="{price_change_4h_class}">{f"{price_change_4h:.2f}%" if pd.notna(price_change_4h) else '-'}</td>
                    <td class="{price_change_24h_class}">{f"{price_change_24h:.2f}%" if pd.notna(price_change_24h) else '-'}</td>
                    <td class="{profit_class}">{f"{profit:.2f}%" if pd.notna(profit) else '-'}</td>
                </tr>""")
            
            html_content.append("</table>")
        else:
            html_content.append("""<div class="warning-box">
                <p>没有可用的告警性能数据记录。</p>
            </div>""")
        
        # 结束HTML
        html_content.append("</body></html>")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
    
    def _add_profit_trend_chart(self, df: pd.DataFrame, html_content: List[str]) -> None:
        """添加收益率趋势图
        
        Args:
            df: 性能数据DataFrame
            html_content: HTML内容列表
        """
        # 确保alert_time列是datetime类型
        df['alert_time'] = pd.to_datetime(df['alert_time'])
        
        # 按时间排序
        df_sorted = df.sort_values('alert_time')
        
        # 检查数据是否存在
        if df_sorted.empty or 'profit_if_follow' not in df_sorted.columns:
            self.logger.warning("没有足够的数据生成收益率趋势图")
            return
            
        # 确保profit_if_follow列中有有效数据
        valid_data = df_sorted.dropna(subset=['profit_if_follow'])
        if valid_data.empty:
            self.logger.warning("profit_if_follow列中没有有效数据")
            return
            
        # 记录数据信息以便调试
        self.logger.info(f"生成收益率趋势图，数据点数量: {len(valid_data)}")
        self.logger.info(f"收益率范围: {valid_data['profit_if_follow'].min():.2f}% 到 {valid_data['profit_if_follow'].max():.2f}%")
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        plt.plot(valid_data['alert_time'], valid_data['profit_if_follow'], marker='o', linestyle='-')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('告警收益率趋势')
        plt.xlabel('时间')
        plt.ylabel('收益率 (%)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        chart_filename = os.path.basename(self._output_path).replace('.html', '_profit_trend_chart.png')
        chart_path = os.path.join(self._output_dir, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        # 添加到HTML
        html_content.append(f"""<div class="chart-container">
            <h2>告警收益率趋势</h2>
            <img src="{chart_filename}" alt="告警收益率趋势" style="width:100%;max-width:800px;">
        </div>""")
    
    def _add_symbol_performance_chart(self, df: pd.DataFrame, html_content: List[str]) -> None:
        """添加按交易对的性能对比图
        
        Args:
            df: 性能数据DataFrame
            html_content: HTML内容列表
        """
        # 检查数据是否存在
        if df.empty or 'display_name' not in df.columns or 'profit_if_follow' not in df.columns:
            self.logger.warning("没有足够的数据生成交易对性能对比图")
            return
            
        # 确保profit_if_follow列中有有效数据
        valid_df = df.dropna(subset=['profit_if_follow', 'display_name'])
        if valid_df.empty:
            self.logger.warning("交易对或收益率数据中没有有效数据")
            return
            
        # 按交易对分组计算平均收益
        try:
            symbol_performance = valid_df.groupby('display_name')['profit_if_follow'].agg(['mean', 'count']).reset_index()
            symbol_performance = symbol_performance.sort_values('mean', ascending=False)
            
            # 显示所有交易对数据，不再过滤记录数量
            # symbol_performance = symbol_performance[symbol_performance['count'] >= 2]
            
            if len(symbol_performance) > 0:
                # 记录数据信息以便调试
                self.logger.info(f"生成交易对性能对比图，交易对数量: {len(symbol_performance)}")
                
                # 创建图表
                plt.figure(figsize=(12, 6))
                bars = plt.bar(symbol_performance['display_name'], symbol_performance['mean'])
                
                # 为正负值设置不同颜色
                for i, bar in enumerate(bars):
                    if symbol_performance['mean'].iloc[i] >= 0:
                        bar.set_color('green')
                    else:
                        bar.set_color('red')
                
                plt.title('各交易对平均收益率')
                plt.xlabel('交易对')
                plt.ylabel('平均收益率 (%)')
                plt.grid(True, axis='y')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            else:
                self.logger.warning("没有足够的交易对数据生成图表（每个交易对至少需要2条记录）")
                return
        except Exception as e:
            self.logger.error(f"生成交易对性能对比图时出错: {e}")
            return
        
        # 保存图表
        chart_filename = os.path.basename(self._output_path).replace('.html', '_symbol_performance_chart.png')
        chart_path = os.path.join(self._output_dir, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        # 添加到HTML
        html_content.append(f"""<div class="chart-container">
            <h2>各交易对平均收益率</h2>
            <img src="{chart_filename}" alt="各交易对平均收益率" style="width:100%;max-width:800px;">
        </div>""")
    
    def _add_score_performance_chart(self, df: pd.DataFrame, html_content: List[str]) -> None:
        """添加按信号分数的性能对比图
        
        Args:
            df: 性能数据DataFrame
            html_content: HTML内容列表
        """
        # 检查数据是否存在
        if df.empty or 'score' not in df.columns or 'profit_if_follow' not in df.columns:
            self.logger.warning("没有足够的数据生成信号分数性能对比图")
            return
            
        # 确保必要列中有有效数据
        valid_df = df.dropna(subset=['profit_if_follow', 'score'])
        if valid_df.empty:
            self.logger.warning("信号分数或收益率数据中没有有效数据")
            return
            
        try:
            # 按信号分数分组计算平均收益
            score_performance = valid_df.groupby('score')['profit_if_follow'].agg(['mean', 'count']).reset_index()
            score_performance = score_performance.sort_values('score')
            
            if len(score_performance) > 0:
                # 记录数据信息以便调试
                self.logger.info(f"生成信号分数性能对比图，分数类别数量: {len(score_performance)}")
                self.logger.info(f"分数范围: {score_performance['score'].min()} 到 {score_performance['score'].max()}")
                
                # 创建图表
                plt.figure(figsize=(10, 6))
                bars = plt.bar(score_performance['score'], score_performance['mean'])
                
                # 为正负值设置不同颜色
                for i, bar in enumerate(bars):
                    if score_performance['mean'].iloc[i] >= 0:
                        bar.set_color('green')
                    else:
                        bar.set_color('red')
                
                plt.title('各信号分数平均收益率')
                plt.xlabel('信号分数')
                plt.ylabel('平均收益率 (%)')
                plt.grid(True, axis='y')
                plt.tight_layout()
            else:
                self.logger.warning("没有足够的信号分数数据生成图表")
                return
        except Exception as e:
            self.logger.error(f"生成信号分数性能对比图时出错: {e}")
            return
        
        # 保存图表
        chart_filename = os.path.basename(self._output_path).replace('.html', '_score_performance_chart.png')
        chart_path = os.path.join(self._output_dir, chart_filename)
        plt.savefig(chart_path)
        plt.close()
        
        # 添加到HTML
        html_content.append(f"""<div class="chart-container">
            <h2>各信号分数平均收益率</h2>
            <img src="{chart_filename}" alt="各信号分数平均收益率" style="width:100%;max-width:800px;">
        </div>""")


def run_performance_analysis(db: Database, days: int = 30, output_path: str = "performance_report.html") -> None:
    """运行性能分析的入口函数
    
    Args:
        db: 数据库实例
        days: 分析最近多少天的数据，默认30天
        output_path: 输出报告的路径
    """
    logger = get_logger()
    try:
        logger.info(f"开始运行性能分析，分析天数: {days}，输出路径: {output_path}")
        analyzer = PerformanceAnalyzer(db)
        analyzer.analyze(days, output_path)
        logger.info("性能分析完成")
    except Exception as e:
        logger.error(f"运行性能分析时发生错误: {e}")
        raise


if __name__ == "__main__":
    # 用于直接运行此脚本进行测试
    from utils.database import Database
    from utils.config_loader import load_config
    
    config = load_config()
    db = Database(config['database_path'])
    run_performance_analysis(db)
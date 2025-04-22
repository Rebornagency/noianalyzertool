"""
Enhanced AI Insights Module for NOI Analyzer

This module generates professional real estate accounting insights from NOI comparison results.
It embodies the personality of a senior real estate accountant with expertise in property financial analysis.
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_insights')

def generate_consolidated_insights(comparison_results: Dict[str, Any], property_name: str = "") -> Dict[str, Any]:
    """
    Generate professional real estate accounting insights from NOI comparison results
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
        property_name: Name of the property for the analysis
        
    Returns:
        Dictionary with professional insights
    """
    logger.info(f"Generating professional insights for property: {property_name}")
    
    insights = {
        "summary": "",
        "performance": [],
        "recommendations": []
    }
    
    # Generate professional summary
    property_prefix = f"Property {property_name}" if property_name else "The subject property"
    
    if "current" in comparison_results:
        current = comparison_results["current"]
        insights["summary"] = f"{property_prefix} reports a Net Operating Income (NOI) of ${current['noi']:,.2f} for the current period. "
        insights["summary"] += f"This reflects total operating revenue of ${current['revenue']:,.2f} against total operating expenses of ${current['expense']:,.2f}. "
        
        # Add NOI margin analysis
        if current['revenue'] > 0:
            noi_margin = (current['noi'] / current['revenue']) * 100
            insights["summary"] += f"The NOI margin stands at {noi_margin:.1f}%, "
            
            if noi_margin > 65:
                insights["summary"] += "which indicates excellent operational efficiency. "
            elif noi_margin > 55:
                insights["summary"] += "reflecting strong operational performance. "
            elif noi_margin > 45:
                insights["summary"] += "which is within industry standard parameters. "
            else:
                insights["summary"] += "suggesting potential opportunities for operational improvement. "
    
    # Generate detailed performance insights with professional accounting terminology
    if "actual_vs_budget" in comparison_results:
        budget_comp = comparison_results["actual_vs_budget"]
        
        if budget_comp["noi_variance"] >= 0:
            insights["performance"].append(
                f"Budget Variance Analysis: NOI exceeds budgetary projections by ${budget_comp['noi_variance']:,.2f} "
                f"({budget_comp['noi_percent_variance']:.1f}% favorable variance). "
                f"This positive performance indicates effective operational management and revenue optimization."
            )
            
            # Add revenue/expense breakdown for positive variance
            if budget_comp["revenue_variance"] > 0 and budget_comp["expense_variance"] < 0:
                insights["performance"].append(
                    f"The favorable NOI variance is attributed to both revenue outperformance (${budget_comp['revenue_variance']:,.2f} above budget) "
                    f"and expense containment (${abs(budget_comp['expense_variance']):,.2f} below budget), "
                    f"demonstrating effective management across both revenue generation and cost control functions."
                )
            elif budget_comp["revenue_variance"] > 0:
                insights["performance"].append(
                    f"The favorable NOI variance is primarily driven by revenue outperformance of ${budget_comp['revenue_variance']:,.2f} above budget "
                    f"({budget_comp['revenue_percent_variance']:.1f}% favorable variance), "
                    f"suggesting successful implementation of revenue optimization strategies."
                )
            elif budget_comp["expense_variance"] < 0:
                insights["performance"].append(
                    f"The favorable NOI variance is primarily attributable to effective expense management, with operating costs "
                    f"${abs(budget_comp['expense_variance']):,.2f} below budgetary allocations "
                    f"({abs(budget_comp['expense_percent_variance']):.1f}% favorable variance)."
                )
        else:
            insights["performance"].append(
                f"Budget Variance Analysis: NOI falls short of budgetary projections by ${abs(budget_comp['noi_variance']):,.2f} "
                f"({abs(budget_comp['noi_percent_variance']):.1f}% unfavorable variance). "
                f"This variance warrants detailed examination of revenue streams and expense categories."
            )
            
            # Add revenue/expense breakdown for negative variance
            if budget_comp["revenue_variance"] < 0 and budget_comp["expense_variance"] > 0:
                insights["performance"].append(
                    f"The unfavorable NOI variance stems from both revenue underperformance (${abs(budget_comp['revenue_variance']):,.2f} below budget) "
                    f"and expense overruns (${budget_comp['expense_variance']:,.2f} above budget), "
                    f"indicating potential operational challenges requiring comprehensive intervention."
                )
            elif budget_comp["revenue_variance"] < 0:
                insights["performance"].append(
                    f"The unfavorable NOI variance is primarily attributable to revenue underperformance of ${abs(budget_comp['revenue_variance']):,.2f} below budget "
                    f"({abs(budget_comp['revenue_percent_variance']):.1f}% unfavorable variance), "
                    f"necessitating a review of rental rates, occupancy strategies, and ancillary income opportunities."
                )
            elif budget_comp["expense_variance"] > 0:
                insights["performance"].append(
                    f"The unfavorable NOI variance is primarily driven by expense overruns of ${budget_comp['expense_variance']:,.2f} above budgetary allocations "
                    f"({budget_comp['expense_percent_variance']:.1f}% unfavorable variance), "
                    f"suggesting a need for enhanced cost control measures and vendor contract reviews."
                )
    
    if "month_vs_prior" in comparison_results:
        mom_comp = comparison_results["month_vs_prior"]
        
        if mom_comp["noi_change"] >= 0:
            insights["performance"].append(
                f"Month-over-Month Analysis: NOI demonstrates a positive trajectory with an increase of ${mom_comp['noi_change']:,.2f} "
                f"({mom_comp['noi_percent_change']:.1f}%) compared to the prior month. "
                f"This sequential improvement reflects effective short-term operational adjustments."
            )
        else:
            insights["performance"].append(
                f"Month-over-Month Analysis: NOI exhibits a decline of ${abs(mom_comp['noi_change']):,.2f} "
                f"({abs(mom_comp['noi_percent_change']):.1f}%) compared to the prior month. "
                f"This sequential deterioration warrants investigation into recent operational changes or market shifts."
            )
    
    if "year_vs_year" in comparison_results:
        yoy_comp = comparison_results["year_vs_year"]
        
        if yoy_comp["noi_change"] >= 0:
            insights["performance"].append(
                f"Year-over-Year Analysis: NOI demonstrates a positive annual trend with an increase of ${yoy_comp['noi_change']:,.2f} "
                f"({yoy_comp['noi_percent_change']:.1f}%) compared to the same period in the prior fiscal year. "
                f"This annual improvement indicates sustainable operational enhancements and potential asset appreciation."
            )
        else:
            insights["performance"].append(
                f"Year-over-Year Analysis: NOI shows a decline of ${abs(yoy_comp['noi_change']):,.2f} "
                f"({abs(yoy_comp['noi_percent_change']):.1f}%) compared to the same period in the prior fiscal year. "
                f"This annual deterioration suggests structural challenges that may impact asset valuation if not addressed."
            )
    
    # Generate professional recommendations with specific actionable insights
    recommendations = []
    
    if "actual_vs_budget" in comparison_results:
        budget_comp = comparison_results["actual_vs_budget"]
        
        if budget_comp["noi_variance"] < 0:
            if budget_comp["revenue_variance"] < 0:
                recommendations.append(
                    "Conduct a comprehensive revenue enhancement analysis to address the unfavorable budget variance. "
                    "Consider reviewing rental rates against market comparables, implementing strategic lease renewal incentives, "
                    "and optimizing ancillary income streams such as parking, laundry, and application fees."
                )
            
            if budget_comp["expense_variance"] > 0:
                recommendations.append(
                    "Implement targeted expense reduction measures focusing on the categories with the largest unfavorable variances. "
                    "Consider renegotiating service contracts, conducting utility consumption audits, and evaluating staffing efficiency "
                    "to bring operational expenses in line with budgetary allocations."
                )
    
    if "month_vs_prior" in comparison_results:
        mom_comp = comparison_results["month_vs_prior"]
        
        if mom_comp["noi_change"] < 0:
            recommendations.append(
                "Perform a detailed month-over-month variance analysis to identify specific revenue and expense categories "
                "driving the sequential NOI decline. Implement immediate corrective actions for any operational issues "
                "and adjust short-term forecasts accordingly."
            )
    
    if "year_vs_year" in comparison_results:
        yoy_comp = comparison_results["year_vs_year"]
        
        if yoy_comp["noi_change"] < 0:
            recommendations.append(
                "Conduct a strategic asset performance review to address the year-over-year NOI decline. "
                "Consider developing a comprehensive capital improvement plan to enhance property competitiveness, "
                "reviewing property positioning within the market, and evaluating management effectiveness."
            )
    
    # Add professional general recommendations
    if len(recommendations) < 3:
        recommendations.append(
            "Implement quarterly budget reforecasting to account for changing market conditions and operational realities. "
            "This practice enhances financial planning accuracy and allows for timely strategic adjustments."
        )
        
        recommendations.append(
            "Develop a preventative maintenance program to optimize the balance between routine maintenance expenses "
            "and capital expenditures. This approach typically reduces long-term operating costs while extending asset life."
        )
        
        recommendations.append(
            "Consider implementing energy efficiency initiatives such as LED lighting retrofits, smart thermostats, and "
            "water conservation measures. These investments typically yield 15-25% utility expense reductions with ROI periods "
            "of 12-36 months, directly enhancing NOI and asset value."
        )
    
    # Ensure we have at least 3 recommendations but no more than 5
    insights["recommendations"] = recommendations[:5]
    
    return insights

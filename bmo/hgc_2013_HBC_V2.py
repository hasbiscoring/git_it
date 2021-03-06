# use HBC_20110101_20131031 for data preparation, the only way to get default if from the population data v15 excel file
# HBC: FACT no MI/UEN(after 2012Oct) + HBC2011_2013(before 2012Oct)
# This file does not have M&I ratings


#!/usr/bin/python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
 
pdIntval = [0.0003, 0.0007, 0.0011, 0.0019, 0.0032, 0.0054, 0.0091, 0.0154, 0.0274, 0.0516, 0.097, 0.1823, 1]
msRating = ['I-2', 'I-3', 'I-4', 'I-5', 'I-6', 'I-7', 'S-1', 'S-2', 'S-3', 'S-4', 'P-1', 'P-2', 'P-3', 'D-1']
pcRR = [10, 15, 20, 25, 30, 35, 40, 45, 46, 47, 50, 51, 52]
ranking = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
newMapPD = [0.0003, 0.0005, 0.0009, 0.0015, 0.0026, 0.0043, 0.0073, 0.0123, 0.0214, 0.0395, 0.0743, 0.1397, 0.2412]
oldMapPD = [0.0004, 0.0007, 0.0013, 0.0025, 0.004, 0.0067, 0.0107, 0.018, 0.0293, 0.0467, 0.0933, 0.18, 0.3333]

# read in 2013 model drivers / rating data from HBC
#bmo2013HBC = pd.read_excel(u"H:\\work\\usgc\\2015\\quant\\2013\\2013_combined_data.xlsx", sheetname = "HBC_20110101_20131031")     #(4083, 91)
#bmo2013HBC.to_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\bmo2013HBC")
bmo2013HBC = pd.read_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\bmo2013HBC")
bmo2013HBC['source_from'] = 'HBC'
varbmo2013HBC = [x.replace(' ', '_').lower() for x in list(bmo2013HBC)]
bmo2013HBC.columns = varbmo2013HBC

bmo2013HBC['quant_ranking'] = np.where(bmo2013HBC.bor_quan_risk_rtg <=52, bmo2013HBC.bor_quan_risk_rtg.map(dict(zip(pcRR, ranking))), 15)
bmo2013HBC['final_ranking'] = np.where(bmo2013HBC.rm_final <=52, bmo2013HBC.rm_final.map(dict(zip(pcRR, ranking))), 15)

# pick from 2012-2-1 to 2012-10-31, since 1)MRA data is in this interval  2)2012-11-1 to 2013-1-31 will be from FACT
bmo2013HBC_1 = bmo2013HBC.ix[(bmo2013HBC.rnd != 'Y') & (bmo2013HBC.eff_dt <= pd.datetime(2013, 1, 31)) & (bmo2013HBC.eff_dt >= pd.datetime(2012, 2, 1)), ['sk_entity_id', 'entity_nm', 'eff_dt', 'fin_stmt_dt', 'source_from', 'input_bsd', 'quant_ranking', 'final_ranking']]
bmo2013HBC_1 = bmo2013HBC_1.rename(columns = {'entity_nm': 'entity_name', 'eff_dt': 'final_form_date'})               #  (2380, 5)

 
#read in the 2013 population data(year start data)  ['uen', 'naics', 'sic', 'ussic', 'dft_date', 'default_flag']  #7635
#bmo2013 = pd.read_excel(u"H:\\work\\usgc\\2015\\quant\\2013\\2013_combined_data.xlsx", sheetname = "2013_population")
#bmo2013.to_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\bmo2013")            # save it
bmo2013 = pd.read_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\bmo2013")
varbmo2013 = [x.replace(' ', '_').lower() for x in list(bmo2013)]
bmo2013.columns = varbmo2013

bmo2013_0 = bmo2013.query('level58_desc != "P&C CANADA" & pd_master_scale == "Commercial" & model == "General Commercial"') 
bmo2013_1 = bmo2013_0.ix[:, ['uen', 'sk_entity_id', 'ussic', 'dft_date', 'default_flag']]
bmo2013_1 = bmo2013_1.rename(columns = {'dft_date': 'default_date'}) 
bmo2013_1['default_flag'] = bmo2013_1.default_flag.replace({'Y':1, 'N': 0})
 

########################     defaults are from the year start file   ###########################
bmo2013HBC_2 = pd.merge(bmo2013HBC_1, bmo2013_1, on = 'sk_entity_id', how = 'inner') 					# left join will give same final result


# read in sic_indust info
sic_indust = pd.read_excel("H:\\work\\usgc\\2015\\quant\\SIC_Code_List.xlsx", sheetname = "sic_indust")

# to get sector_group and remove by sic
bmo2013HBC_2['indust'] = bmo2013HBC_2.ussic.replace(dict(zip(sic_indust.sic_code, sic_indust.indust)))
bmo2013HBC_2['sector_group'] = bmo2013HBC_2.ussic.replace(dict(zip(sic_indust.sic_code, sic_indust.sector_group))) 
bmo2013HBC_2_after_sic = bmo2013HBC_2.query('sector_group not in ["NONP", "AGRI", "AGSM", "OTHR", "FOST"]') 

# sort for PW
bmo2013HBC_2_after_sic.sort(['uen', 'default_flag', 'final_form_date'], ascending = [True, False, True], inplace = True)
 
#final data after sic, pw 
bmo2013HBC_2_after_sic_pw = bmo2013HBC_2_after_sic.drop_duplicates('uen') 											# {0:687, 1: 20}
bmo2013HBC_2_after_sic_pw.default_flag.value_counts()
bmo2013HBC_2_after_sic_pw = bmo2013HBC_2_after_sic_pw.rename(columns = {'ussic': 'us_sic'})

# Almost none F2013 HBC having all financial statements, we need to go to MRA to pull them.
#mra = pd.read_excel("R:\\Global_Market_Risk\RCST\\WCM\Huiming_Song\\data\\DCU_MRA_RISK_SPREAD_D.xls", sheetname = "DCU_MRA_RISK_SPREAD_D")
#mra.to_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\MRA_DATA")
mra = pd.read_pickle(u"H:\\work\\usgc\\2015\\quant\\2013\\MRA_DATA")
mrakeep = ['sk_entity_id', 'as_of_dt', 'cur_ast_amt', 'tot_ast_amt', 'cur_liab_amt', 'tot_liab_amt', 'tot_debt_amt', 'net_worth_amt', 'tangible_net_worth_amt', 'tot_sales_amt', 'net_inc_amt', 'ebitda_amt', 'tot_debt_srvc_amt', 'ebit_amt', 'cash_and_secu_amt', 'debt_srvc_cov_rto', 'debt_to_tnw_rto', 'debt_to_ebitda_rto']
mra_1 = mra.ix[:, mrakeep]
mra_1_vars = [x.replace(' ', '_').lower() for x in list(mra_1)]
mra_1.columns = mra_1_vars

bmo2013HBC_2_after_sic_pw_mra = pd.merge(bmo2013HBC_2_after_sic_pw, mra_1, left_on = ['sk_entity_id'], right_on = ['sk_entity_id'], how = 'inner')
bmo2013HBC_2_after_sic_pw_mra['dt_diff'] = abs((bmo2013HBC_2_after_sic_pw_mra.final_form_date - bmo2013HBC_2_after_sic_pw_mra.as_of_dt) / np.timedelta64(1, 'D'))
bmo2013HBC_2_after_sic_pw_mra['mra_priority'] = np.where(bmo2013HBC_2_after_sic_pw_mra['dt_diff'] == 0, 1, np.where(bmo2013HBC_2_after_sic_pw_mra['dt_diff'] <= 30, 2, np.where(bmo2013HBC_2_after_sic_pw_mra['dt_diff'] <= 50, 3, 4)))
# pick same data(pri=0) first, then 30 day(pri=2), and so on
bmo2013HBC_2_after_sic_pw_mra.sort(['uen', 'mra_priority'], ascending = [True, True], inplace = True)      
print bmo2013HBC_2_after_sic_pw_mra.drop_duplicates('uen').mra_priority.value_counts()
print bmo2013HBC_2_after_sic_pw_mra.drop_duplicates('uen').query('default_flag == 1').mra_priority.value_counts()
bmo2013HBC_2_after_sic_pw_mra_dudup = bmo2013HBC_2_after_sic_pw_mra.drop_duplicates('uen')
print bmo2013HBC_2_after_sic_pw_mra_dudup.drop_duplicates('uen').query('default_flag == 1').mra_priority.value_counts()
bmo2013HBC_2_after_sic_pw_mra_dudup['bsd'] = bmo2013HBC_2_after_sic_pw_mra_dudup.input_bsd.apply(lambda x: pd.to_datetime(x))
bmo2013HBC_2_after_sic_pw_mra_dudup['dsc'] = bmo2013HBC_2_after_sic_pw_mra_dudup['debt_srvc_cov_rto']

## table19_calc:  Non-Debt Based Ratios ( except Net Margin, EBITDA Margin, EBIT Margin)
def table19_calc(x, y):
	return np.where((x.isnull()) | (y.isnull()), np.nan, np.where((x == 0) & (y == 0), 0, np.where((x > 0) & (y == 0), 99999999, np.where((x < 0) & (y == 0), -99999999, np.where((x < 0) & (y < 0), -99999999, x / y )))))

# years in business 	
def yib_calc(x, y):
	return (x - y) / np.timedelta64(1, 'Y')
	
# cur_rto = cur_ast_amt/cur_liab_amt:   							# table 19
# debt_to_tnw_rto = tot_debt_amt / tangible_net_worth_amt			# table 19
# yrs_in_bus  =  final_form_date - bsd								# direct calc
# net_margin_rto =  net_inc_amt / tot_sales_amt						# table 19

 
#years in business
bmo2013HBC_2_after_sic_pw_mra_dudup['yrs_in_bus'] = yib_calc(bmo2013HBC_2_after_sic_pw_mra_dudup.final_form_date, bmo2013HBC_2_after_sic_pw_mra_dudup.bsd)

#current ratio = current assets / current liability
bmo2013HBC_2_after_sic_pw_mra_dudup['cur_rto'] = table19_calc(bmo2013HBC_2_after_sic_pw_mra_dudup.cur_ast_amt, bmo2013HBC_2_after_sic_pw_mra_dudup.cur_liab_amt)

#net margin ratio = net income / total sales
bmo2013HBC_2_after_sic_pw_mra_dudup['net_margin_rto'] = table19_calc(bmo2013HBC_2_after_sic_pw_mra_dudup.net_inc_amt, bmo2013HBC_2_after_sic_pw_mra_dudup.tot_sales_amt)
bmo2013HBC_2_after_sic_pw_mra_dudup['yeartype'] = '2013HGC'
# delete the obligor whose as_of_dt diffs more than 30 days
bmo2013HBC_2_final = bmo2013HBC_2_after_sic_pw_mra_dudup.ix[bmo2013HBC_2_after_sic_pw_mra_dudup.mra_priority.isin([1, 2]), :]

print ".99 percentile is %s" %(np.percentile(bmo2013HBC_2_after_sic_pw_mra_dudup['net_margin_rto'], 99)) 





#######################################################   STOP HERE  #############################################################



#after it is done, concat with bmo2013_FACT_after_sic_pw in hgc_2013_FACT.py for final dedup
bmo2013_all = pd.concat([bmo2013HBC_2_final, bmo2013_FACT_after_sic_pw], axis = 0)
bmo2013_all.sort(['uen', 'default_flag', 'final_form_date'], ascending = [True, False, True], inplace = True)

# finally we get 1774 obligors, compared with v15 data which gives 1619 after pw and sic
bmo2013_final = bmo2013_all.drop_duplicates('uen')  																# {0: 1740, 1: 34}
print bmo2013_final.default_flag.value_counts(dropna = False)






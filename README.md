# q_nlloc
Routine NLLoc processing for several input model

1. Copy model file into "input/mod" folder
2. Set standar control on "base.in" (except ======= ====== area)
3. Place phase data to "phase.obs" and station data to "station.dat" (NLLoc accepted format)
4. Run_NLLoc() from python >= 3.6 with option: x_len=500, y_len=300, z_len=100 (area search volume with center on control file)


Output is input for Velest/q_velest and several gmt data for plotting using q_plot



### requirements
* check_outliers module from q_modul
* velest_rw and nlloc_rw from q_convert

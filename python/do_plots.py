#!/usr/bin/env python
"""
Create plots out of the histograms produced in previous stages
"""
import sys
import os
import os.path
import ntpath
import importlib
import copy
import re
import logging
import ROOT  # type: ignore
import pandas as pd
import array
import math

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


LOGGER = logging.getLogger("FCCAnalyses.plot")


# _____________________________________________________________________________
def removekey(d: dict, key: str) -> dict:
    """
    Remove dictionary element.
    """
    r = dict(d)
    del r[key]
    return r


def sorted_dict_values(dic: dict) -> list:
    """'
    Sort values in the dictionary.
    """
    keys = sorted(dic)
    return [dic[key] for key in keys]


def formatStatUncHist(hists, name, hstyle=3254):
    hist_tot = hists[0].Clone(name + "_unc")
    for h in hists[1:]:
        hist_tot.Add(h)
    hist_tot.SetFillColor(ROOT.kBlack)
    hist_tot.SetMarkerSize(0)
    hist_tot.SetLineWidth(0)
    hist_tot.SetFillStyle(hstyle)
    return hist_tot


# _____________________________________________________________________________
def determine_lumi_scaling(config: dict[str, any], infile: object, initial_scale: float = 1.0) -> float:
    """
    Determine whether to (re)scale histograms in the file to luminosity.
    """
    scale: float = initial_scale

    # Check if histograms were already scaled to lumi
    try:
        scaled: bool = infile.scaled.GetVal()
    except AttributeError:
        LOGGER.error(
            "Input file does not contain scaling " "information!\n  %s\nAborting...",
            infile.GetName(),
        )
        sys.exit(3)

    print("found scaling", scaled)
    if scaled:
        try:
            int_lumi_in_file: float = infile.intLumi.GetVal()
        except AttributeError:
            LOGGER.error(
                "Can not load integrated luminosity " "value from the input file!\n  %s\n" "Aborting...",
                infile.GetName(),
            )

        if config["int_lumi"] != int_lumi_in_file:
            LOGGER.warning(
                "Histograms are already scaled to different "
                "luminosity value!\n"
                "Luminosity in the input file is %s pb-1 and "
                "luminosity requested in plots script is %s pb-1.",
                int_lumi_in_file,
                config["int_lumi"],
            )
            if config["do_scale"]:
                LOGGER.warning(
                    "Rescaling from %s pb-1 to %s pb-1...",
                    int_lumi_in_file,
                    config["int_lumi"],
                )
                scale *= config["int_lumi"] / int_lumi_in_file

    else:
        if config["do_scale"]:
            scale = scale * config["int_lumi"]

    return scale


# _____________________________________________________________________________
def load_hists(var: str, label: str, sel: str, config: dict[str, any], rebin: int) -> tuple[dict[str, any], dict[str:any]]:
    """
    Load all histograms needed for the plot
    """

    try:
        signal = config["plots"][label]["signal"]
    except KeyError:
        signal = {}

    try:
        backgrounds = config["plots"][label]["backgrounds"]
    except KeyError:
        backgrounds = {}

    hsignal = {}
    for s in signal:
        hsignal[s] = []
        for filepathstem in signal[s]:
            infilepath = config["input_dir"] + filepathstem + "_" + sel + "_histo.root"
            if not os.path.isfile(infilepath):
                LOGGER.info('File "%s" not found!\nSkipping it...', infilepath)
                continue

            with ROOT.TFile(infilepath, "READ") as infile:
                hist = copy.deepcopy(infile.Get(var))
                hist.SetDirectory(0)

                scale = determine_lumi_scaling(config, infile, config["scale_sig"])
            hist.Scale(scale)
            hist.Rebin(rebin)

            if len(hsignal[s]) == 0:
                hsignal[s].append(hist)
            else:
                hist.Add(hsignal[s][0])
                hsignal[s][0] = hist

    hbackgrounds = {}
    for b in backgrounds:
        hbackgrounds[b] = []
        for filepathstem in backgrounds[b]:
            infilepath = config["input_dir"] + filepathstem + "_" + sel + "_histo.root"
            if not os.path.isfile(infilepath):
                LOGGER.info('File "%s" not found!\nSkipping it...', infilepath)
                continue

            with ROOT.TFile(infilepath) as infile:
                hist = copy.deepcopy(infile.Get(var))
                hist.SetDirectory(0)

                scale = determine_lumi_scaling(config, infile, config["scale_bkg"])
            hist.Scale(scale)
            hist.Rebin(rebin)

            if len(hbackgrounds[b]) == 0:
                hbackgrounds[b].append(hist)
            else:
                hist.Add(hbackgrounds[b][0])
                hbackgrounds[b][0] = hist

    for s in hsignal:
        if len(hsignal[s]) == 0:
            hsignal = removekey(hsignal, s)

    for b in hbackgrounds:
        if len(hbackgrounds[b]) == 0:
            hbackgrounds = removekey(hbackgrounds, b)

    return hsignal, hbackgrounds


# _____________________________________________________________________________
def mapHistosFromHistmaker(config: dict[str, any], hist_name: str, param, hist_cfg):

    rebin = hist_cfg["rebin"] if "rebin" in hist_cfg else 1
    # LOGGER.info("Get histograms for %s", hist_name)

    signal = param.procs.get("signal", {})
    backgrounds = param.procs.get("backgrounds", {})
    scaleSig = hist_cfg["scaleSig"] if "scaleSig" in hist_cfg else 1
    normalize = hist_cfg.get("density", False)

    # print(param.inputDir)
    hsignal = {}
    for s in signal:
        hsignal[s] = []
        for f in signal[s]:
            fin = f"{param.inputDir}/{f}.root"
            if not os.path.isfile(fin):
                LOGGER.info('File "%s" not found!\nSkipping it...', fin)
                continue

            with ROOT.TFile(fin) as tf:
                # print(f"Getting histogram {hist_name} from {fin}")
                h = tf.Get(hist_name)
                hh = copy.deepcopy(h)
                hh.SetDirectory(0)
            # LOGGER.info("ScaleSig: %g", scaleSig)
            hh.Scale(param.intLumi * scaleSig)
            hh.Rebin(rebin)
            if len(hsignal[s]) == 0:
                hsignal[s].append(hh)
            else:
                hh.Add(hsignal[s][0])
                hsignal[s][0] = hh

    hbackgrounds = {}
    for b in backgrounds:
        hbackgrounds[b] = []
        for f in backgrounds[b]:
            fin = f"{param.inputDir}/{f}.root"
            if not os.path.isfile(fin):
                LOGGER.info('File "%s" not found!\nSkipping it...', fin)
                continue

            with ROOT.TFile(fin) as tf:
                # print(f"Getting histogram {hist_name} from {fin}")
                h = tf.Get(hist_name)
                hh = copy.deepcopy(h)
                hh.SetDirectory(0)
            hh.Scale(param.intLumi)
            hh.Rebin(rebin)

            if len(hbackgrounds[b]) == 0:
                hbackgrounds[b].append(hh)
            else:
                hh.Add(hbackgrounds[b][0])
                hbackgrounds[b][0] = hh

    for s in list(hsignal.keys()):
        if len(hsignal[s]) == 0:
            del hsignal[s]

    for b in list(hbackgrounds.keys()):
        if len(hbackgrounds[b]) == 0:
            del hbackgrounds[b]

    if not hsignal:
        LOGGER.error("No signal input files found!\nAborting...")
        sys.exit(3)





    return hsignal, hbackgrounds

def find_empty_bins(histo):
    # --- merge last empty bins  ---
    empty_bin_indices = []
    nbins0 = histo.GetNbinsX()

    for i in range(nbins0, 0, -1):
        if histo.GetBinContent(i) == 0:
            empty_bin_indices.append(i)
        else:
            # 'i' is now the first non-empty bin from the end: we merge all bins from i+1 to nbins0 with bin i
            merge_index = i
            break

    print("Empty bin indices in histos[0]:", empty_bin_indices)
    print("Merging bins from", merge_index+1, "to", nbins0, "into bin", merge_index)

    return empty_bin_indices, merge_index
 

def rebin_last_empty_bins(histo, empty_bin_indices, merge_index):

    nbins0 = histo.GetNbinsX()
    #  Define new binning using the merge_index ---
    new_bin_edges = []
    for i in range(1, merge_index+1):
        new_bin_edges.append(histo.GetBinLowEdge(i))
    # Append the upper edge of the last bin (bin nbins0+1)
    new_bin_edges.append(histo.GetBinLowEdge(nbins0+1))

    # Convert Python list to array of doubles for ROOT
    new_bin_edges_arr = array.array('d', new_bin_edges)

    # --- Step 3: Create new histograms with the new binning ---
    new_name = histo.GetName() + "_rebinned"
    new_title = histo.GetTitle() + " (rebinned)"
    new_hist = ROOT.TH1F(new_name, new_title, len(new_bin_edges_arr)-1, new_bin_edges_arr)
    
    # Copy original bin contents for bins before the merge_index
    for b in range(1, merge_index):
        new_hist.SetBinContent(b, histo.GetBinContent(b))
        new_hist.SetBinError(b, histo.GetBinError(b))
    
    # For the merged bin (at index merge_index in the new histogram),
    # sum the contents (and errors in quadrature) from bins merge_index to nbins0
    merged_content = 0.0
    merged_error2 = 0.0
    for b in range(merge_index, nbins0+1):
        merged_content += histo.GetBinContent(b)
        merged_error2 += (histo.GetBinError(b))**2
    new_hist.SetBinContent(merge_index, merged_content)
    new_hist.SetBinError(merge_index, math.sqrt(merged_error2))
    
    return new_hist



# _____________________________________________________________________________
def runPlots(
    config: dict[str, any],
    args,
    var,
    sel,
    script_module,
    hsignal,
    hbackgrounds,
    extralab,
):

    # Below are settings for separate signal and background legends
    if config["split_leg"]:
        legsize = 0.04 * (len(hsignal))
        legsize2 = 0.04 * (len(hbackgrounds))
        leg = ROOT.TLegend(0.15, 0.60 - legsize, 0.50, 0.62)
        leg2 = ROOT.TLegend(0.60, 0.60 - legsize2, 0.88, 0.62)

        if config["leg_position"][0] is not None and config["leg_position"][2] is not None:
            leg.SetX1(config["leg_position"][0])
            leg.SetX2((config["leg_position"][0] + config["leg_position"][2]) / 2)
            leg2.SetX2((config["leg_position"][0] + config["leg_position"][2]) / 2)
            leg2.SetX2(config["leg_position"][0])
        if config["leg_position"][1] is not None:
            leg.SetY1(config["leg_position"][1])
            leg2.SetY1(config["leg_position"][1])
        if config["leg_position"][3] is not None:
            leg.SetY2(config["leg_position"][3])
            leg2.SetY2(config["leg_position"][3])

        leg2.SetFillColor(0)
        leg2.SetFillStyle(0)
        leg2.SetLineColor(0)
        leg2.SetShadowColor(10)
        leg2.SetTextSize(config["legend_text_size"])
        leg2.SetTextFont(42)
    else:
        legsize = 0.04 * (len(hbackgrounds) + len(hsignal))
        leg = ROOT.TLegend(0.60, 0.86 - legsize, 0.96, 0.88)
        leg2 = None

        if config["leg_position"][0] is not None:
            leg.SetX1(config["leg_position"][0])
        if config["leg_position"][1] is not None:
            leg.SetY1(config["leg_position"][1])
        if config["leg_position"][2] is not None:
            leg.SetX2(config["leg_position"][2])
        if config["leg_position"][3] is not None:
            leg.SetY2(config["leg_position"][3])

    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetLineColor(0)
    leg.SetShadowColor(10)
    leg.SetTextSize(config["legend_text_size"])
    leg.SetTextFont(42)

    for s in hsignal:
        leg.AddEntry(hsignal[s][0], script_module.legend[s], "l")

    for b in hbackgrounds:
        if config["split_leg"]:
            leg2.AddEntry(hbackgrounds[b][0], script_module.legend[b], "f")
        else:
            leg.AddEntry(hbackgrounds[b][0], script_module.legend[b], "f")

    yields = {}
    for s in hsignal:
        yields[s] = [
            script_module.legend[s],
            hsignal[s][0].Integral(0, -1),
            hsignal[s][0].GetEntries(),
        ]
    for b in hbackgrounds:
        yields[b] = [
            script_module.legend[b],
            hbackgrounds[b][0].Integral(0, -1),
            hbackgrounds[b][0].GetEntries(),
        ]

    histos = []
    colors = []

    nsig = len(hsignal)
    nbkg = len(hbackgrounds)

    for sig in hsignal:
        histos.append(hsignal[sig][0])
        colors.append(script_module.colors[sig])

    for bkg in hbackgrounds:
        histos.append(hbackgrounds[bkg][0])
        colors.append(script_module.colors[bkg])

    lt = "FCC-hh Simulation (Delphes)"
    rt = f"#sqrt{{s}} = {script_module.energy:.1f} TeV,   " f'{config["int_lumi_label"]}'

    if "ee" in script_module.collider:
        lt = "FCC-ee Simulation"
        rt = f"#sqrt{{s}} = {script_module.energy:.1f} GeV,   " f'{config["int_lumi_label"]}'

    customLabel = ""
    try:
        customLabel = script_module.customLabel
    except AttributeError:
        LOGGER.debug("No custom label, using nothing...")

    if "AAAyields" in var:
        drawStack(
            config,
            var,
            "events",
            leg,
            lt,
            rt,
            script_module.formats,
            script_module.outdir + "/" + sel,
            False,
            True,
            histos,
            colors,
            script_module.ana_tex,
            extralab,
            customLabel,
            nsig,
            nbkg,
            leg2,
            yields,
            config["plot_stat_unc"],
        )
        return

    if "stack" in script_module.stacksig:
        if "lin" in script_module.yaxis:
            drawStack(
                config,
                var + "_stack_lin",
                "events",
                leg,
                lt,
                rt,
                script_module.formats,
                script_module.outdir + "/" + sel,
                False,
                True,
                histos,
                colors,
                script_module.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                config["plot_stat_unc"],
            )
        if "log" in script_module.yaxis:
            drawStack(
                config,
                var + "_stack_log",
                "events",
                leg,
                lt,
                rt,
                script_module.formats,
                script_module.outdir + "/" + sel,
                True,
                True,
                histos,
                colors,
                script_module.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                config["plot_stat_unc"],
            )
        if "lin" not in script_module.yaxis and "log" not in script_module.yaxis:
            LOGGER.info("Unrecognized option in formats, should be " "['lin','log']")

    if "nostack" in script_module.stacksig:
        if "lin" in script_module.yaxis:
            drawStack(
                config,
                var + "_nostack_lin",
                "events",
                leg,
                lt,
                rt,
                script_module.formats,
                script_module.outdir + "/" + sel,
                False,
                False,
                histos,
                colors,
                script_module.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                config["plot_stat_unc"],
            )
        if "log" in script_module.yaxis:
            drawStack(
                config,
                var + "_nostack_log",
                "events",
                leg,
                lt,
                rt,
                script_module.formats,
                script_module.outdir + "/" + sel,
                True,
                False,
                histos,
                colors,
                script_module.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                config["plot_stat_unc"],
            )
        if "lin" not in script_module.yaxis and "log" not in script_module.yaxis:
            LOGGER.info("Unrecognised option in formats, should be " "['lin','log']")
    if "stack" not in script_module.stacksig and "nostack" not in script_module.stacksig:
        LOGGER.info("Unrecognized option in stacksig, should be " "['stack','nostack']")


# _____________________________________________________________________________
def runPlotsHistmaker(config: dict[str, any], args, hist_name: str, param, hist_cfg):

    output = hist_cfg["output"]
    print(param)
    hsignal, hbackgrounds = mapHistosFromHistmaker(config, hist_name, param, hist_cfg)

    # only plot requested processes
    if "processes" in hist_cfg:
        hsignal = {k: v for k, v in hsignal.items() if k in hist_cfg["processes"]}
        hbackgrounds = {k: v for k, v in hbackgrounds.items() if k in hist_cfg["processes"]}

    # treat everything as signal if density true
    # merge two dicts into signal and empty background
    normalize = hist_cfg.get("density", False)
    if normalize:
        hsignal.update(hbackgrounds)
        hbackgrounds = {}

    if hasattr(param, "splitLeg"):
        splitLeg = param.splitLeg
    else:
        splitLeg = False

    if hasattr(param, "plotStatUnc"):
        plotStatUnc = param.plotStatUnc
    else:
        plotStatUnc = False

    # Below are settings for separate signal and background legends
    if splitLeg:
        legsize = 0.04 * (len(hsignal))
        legsize2 = 0.04 * (len(hbackgrounds))
        legCoord = [0.15, 0.60 - legsize, 0.50, 0.62]
        leg2 = ROOT.TLegend(0.60, 0.60 - legsize2, 0.88, 0.62)
        leg2.SetFillColor(0)
        leg2.SetFillStyle(0)
        leg2.SetLineColor(0)
        leg2.SetShadowColor(10)
        leg2.SetTextSize(config["legend_text_size"])
        leg2.SetTextFont(42)
    else:
        legsize = 0.04 * (len(hbackgrounds) + len(hsignal))
        legCoord = [0.55, 0.86 - legsize, 0.92, 0.88]
        try:
            legCoord = param.legendCoord
        except AttributeError:
            LOGGER.debug("No legCoord, using default one...")
            legCoord = [0.62, 0.86 - legsize, 0.86, 0.88]
        leg2 = None

    leg = ROOT.TLegend(
        (config["leg_position"][0] if config["leg_position"][0] is not None else legCoord[0]),
        (config["leg_position"][1] if config["leg_position"][1] is not None else legCoord[1]),
        (config["leg_position"][2] if config["leg_position"][2] is not None else legCoord[2]),
        (config["leg_position"][3] if config["leg_position"][3] is not None else legCoord[3]),
    )
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetLineColor(0)
    leg.SetShadowColor(10)
    leg.SetTextSize(config["legend_text_size"])
    leg.SetTextFont(42)

    yields = {}
    for s in hsignal:
        yields[s] = [
            param.legend[s],
            hsignal[s][0].Integral(0, -1),
            hsignal[s][0].GetEntries(),
        ]
    for b in hbackgrounds:
        yields[b] = [
            param.legend[b],
            hbackgrounds[b][0].Integral(0, -1),
            hbackgrounds[b][0].GetEntries(),
        ]

    if hist_name == "cutFlow":
        cutFlowHist = hsignal[list(hsignal.keys())[0]][0]

        funcs = cutFlowHist.GetListOfFunctions()
        for item in funcs:
            if item.InheritsFrom("TObjString"):
                saved_selections = item.GetString().Data()
                print("Selections were:")
                print(saved_selections)
                hist_cfg["xtitle"] = saved_selections.split("\n")
                break

        extract_cutflow_data(param, hist_name, hist_cfg, hsignal, hbackgrounds)

    histos = []
    colors = []

    nsig = len(hsignal)
    nbkg = len(hbackgrounds)
    
    empty_bin_indices, merge_index = [], -1
    # assume signal first proc 
    for proc in hist_cfg["processes"]:
        if proc in hsignal:
            empty_bin_indices, merge_index = find_empty_bins(hsignal[proc][0])

    for proc in hist_cfg["processes"]:
        if proc in hsignal:            
            histo = hsignal[proc][0]
            histo = rebin_last_empty_bins(histo, empty_bin_indices, merge_index)
            histos.append(histo)
            colors.append(param.colors[proc])
            if hist_cfg.get("scaleSig", None):
                signal_legend = f"{param.legend[proc]} x {int(hist_cfg['scaleSig'])}"
            leg.AddEntry(histo, param.legend[proc], "l")

        elif proc in hbackgrounds:
            histo = hbackgrounds[proc][0]
            histo = rebin_last_empty_bins(histo, empty_bin_indices, merge_index)
            histos.append(histo)
            colors.append(param.colors[proc])
            if splitLeg:
                leg2.AddEntry(histo, param.legend[[proc]], "f")
            else:
                leg.AddEntry(histo, param.legend[proc], "f")

    # for s in hsignal:
    #     signal_legend = param.legend[s]
    #     if hist_cfg.get("scaleSig", None):
    #         signal_legend = f"{param.legend[s]} x {int(hist_cfg['scaleSig'])}"
    #     leg.AddEntry(hsignal[s][0], signal_legend, "l")

    # for b in hbackgrounds:
    #     if splitLeg:
    #         leg2.AddEntry(hbackgrounds[b][0], param.legend[b], "f")
    #     else:
    #         leg.AddEntry(hbackgrounds[b][0], param.legend[b], "f")
    
    xtitle = hist_cfg["xtitle"] if "xtitle" in hist_cfg else ""
    ytitle = hist_cfg["ytitle"] if "ytitle" in hist_cfg else "Events"
    xmin = hist_cfg["xmin"] if "xmin" in hist_cfg else -1
    xmax = hist_cfg["xmax"] if "xmax" in hist_cfg else -1
    ymin = hist_cfg["ymin"] if "ymin" in hist_cfg else -1
    ymax = hist_cfg["ymax"] if "ymax" in hist_cfg else -1
    stack = hist_cfg["stack"] if "stack" in hist_cfg else False
    logy = hist_cfg["logy"] if "logy" in hist_cfg else False
    extralab = hist_cfg["extralab"] if "extralab" in hist_cfg else ""

    intLumiab = param.intLumi / 1e06
    intLumi = f"L = {intLumiab:.0f} ab^{{-1}}"
    if hasattr(param, "intLumiLabel"):
        intLumi = getattr(param, "intLumiLabel")

    lt = "FCC-hh Simulation (Delphes)"
    rt = f"#sqrt{{s}} = {param.energy} TeV, {intLumi}"

    if "ee" in param.collider:
        lt = "FCC-ee Simulation"
        rt = f"#sqrt{{s}} = {param.energy} GeV,   {intLumi}"

    customLabel = ""
    try:
        customLabel = param.customLabel
    except AttributeError:
        LOGGER.debug("No customLabel, using nothing...")

    if stack:
        if logy:
            drawStack(
                param,
                config,
                output,
                ytitle,
                leg,
                lt,
                rt,
                param.formats,
                param.outdir,
                True,
                True,
                histos,
                colors,
                param.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                plotStatUnc,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                xtitle=xtitle,
            )
        else:
            drawStack(
                param,
                config,
                output,
                ytitle,
                leg,
                lt,
                rt,
                param.formats,
                param.outdir,
                False,
                True,
                histos,
                colors,
                param.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                plotStatUnc,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                xtitle=xtitle,
            )

    else:
        if logy:
            drawStack(
                param,
                config,
                output,
                ytitle,
                leg,
                lt,
                rt,
                param.formats,
                param.outdir,
                True,
                False,
                histos,
                colors,
                param.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                plotStatUnc,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                xtitle=xtitle,
            )
        else:
            drawStack(
                param,
                config,
                output,
                ytitle,
                leg,
                lt,
                rt,
                param.formats,
                param.outdir,
                False,
                False,
                histos,
                colors,
                param.ana_tex,
                extralab,
                customLabel,
                nsig,
                nbkg,
                leg2,
                yields,
                plotStatUnc,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                xtitle=xtitle,
            )


# ________________________________________________________________________________________
def runPlotsHistmaker2D(config: dict[str, any], args, hist_name: str, param, hist_cfg):

    # Extract parameters from the configuration dictionary
    output_base = hist_cfg.get("output", "output")
    xtitle = hist_cfg.get("xtitle", "")
    ytitle = hist_cfg.get("ytitle", hist_cfg.get("ytile", ""))  # fallback if key is 'ytile'

    # Retrieve axis ranges only if they exist; if not, leave them None
    xmin = hist_cfg.get("xmin", None)
    xmax = hist_cfg.get("xmax", None)
    ymin = hist_cfg.get("ymin", None)
    ymax = hist_cfg.get("ymax", None)

    # Retrieve z range if specified
    zmin = hist_cfg.get("zmin", None)
    zmax = hist_cfg.get("zmax", None)

    logz = hist_cfg.get("logz", False)
    processes = hist_cfg.get("processes", [])

    signal, backgrounds = mapHistosFromHistmaker(config, hist_name, param, hist_cfg)

    LOGGER.info("Get histograms for %s", hist_name)

    for proc in processes:
        output_name = f"{output_base}_{proc}"

        hist = signal.get(proc, None)
        if not hist:
            hist = backgrounds.get(proc, None)

        # If hist is a list of histograms, sum them up
        if isinstance(hist, list):
            if not hist:  # empty list check
                print(f"Warning: No histograms for {hist_name} and process {proc}")
                continue
            sumHist = hist[0].Clone()
            sumHist.SetDirectory(0)
            for h in hist[1:]:
                sumHist.Add(h)
            hist = sumHist

        if not hist:
            print(f"Warning: histogram {hist_name} not found for process {proc}")
            continue

        # check integral integral
        nBinsX = hist.GetNbinsX()
        nBinsY = hist.GetNbinsY()
        integral = hist.Integral(0, nBinsX + 1, 0, nBinsY + 1)
        # print("Integral (including under/overflow):", integral)

        # Create a canvas
        c = ROOT.TCanvas("c", "c", 800, 800)
        c.SetLeftMargin(0.15)
        c.SetRightMargin(0.15)

        # Set logz if required
        if logz:
            c.SetLogz()

        # Adjust axis titles
        hist.GetXaxis().SetTitle(xtitle)
        hist.GetYaxis().SetTitle(ytitle)
        hist.SetTitle("")  # remove general title if desired

        # Set axis ranges if specified
        if xmin is not None and xmax is not None:
            hist.GetXaxis().SetRangeUser(xmin, xmax)
        if ymin is not None and ymax is not None:
            hist.GetYaxis().SetRangeUser(ymin, ymax)

        # Set z range if specified
        if zmin is not None:
            hist.SetMinimum(zmin)
        if zmax is not None:
            hist.SetMaximum(zmax)

        # Draw the histogram with "COLZ" option
        hist.Draw("COLZ")

        # Prepare luminosity label
        intLumiab = param.intLumi / 1e06
        intLumi = f"L = {intLumiab:.0f} ab^{{-1}}"
        if hasattr(param, "intLumiLabel"):
            intLumi = getattr(param, "intLumiLabel")

        leftText = "FCC-hh Simulation (Delphes)"
        rightText = f"#sqrt{{s}} = {param.energy:.1f} TeV,   {intLumi}"

        if "ee" in param.collider:
            leftText = "FCC-ee Simulation"
            rightText = f"#sqrt{{s}} = {param.energy:.1f} GeV,   {intLumi}"

        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAlign(11)
        latex.SetTextSize(0.03)

        text = leftText
        latex.DrawLatex(0.15, 0.91, text)

        latex.SetTextAlign(31)
        latex.SetTextSize(0.03)

        text = "#bf{" + rightText + "}"
        latex.DrawLatex(0.90, 0.91, text)

        # Update canvas and save the plot
        c.Update()

        for f in param.formats:
            out_file = os.path.join(param.outdir, output_name) + "." + f
            c.SaveAs(out_file)

        c.Close()

    return 0


# _____________________________________________________________________________
def extract_cutflow_data(param, hist_name, hist_cfg, hsignal, hbackgrounds):
    import pandas as pd
    import numpy as np
    import os
    import subprocess

    pd.set_option("display.max_colwidth", None)
    if hist_name != "cutFlow":
        raise ValueError('This function only works for "cutFlow".')

    def round_to_significant(x, sig_digits=4):
        if x == 0:
            return 0
        return int(round(x, -int(np.floor(np.log10(abs(x)))) + (sig_digits - 1)))

    def sanitize_latex(text):
        # Replace '#' and 'ˆ' if needed
        if not isinstance(text, str):
            return text
        text = text.replace("#", "\\")
        text = text.replace("ˆ", "^")
        text = text.replace(" ", "\,")
        return text

    data = []
    signal_names = list(hsignal.keys())
    background_names = list(hbackgrounds.keys())

    for i, label in enumerate(hist_cfg["xtitle"]):
        process_yields = {}

        total_signal_yield = sum(hsignal[s][0].Integral(i + 1, i + 1) for s in signal_names)
        total_background_yield = sum(hbackgrounds[b][0].Integral(i + 1, i + 1) for b in background_names)

        for s in signal_names:
            yield_val = hsignal[s][0].Integral(i + 1, i + 1)
            initial_yield = hsignal[s][0].Integral(1, 1)
            efficiency = (yield_val / initial_yield * 100) if (i > 0 and initial_yield != 0) else 100.0
            process_yields[s] = f"{round_to_significant(yield_val)} ({efficiency:.1f})%"

        for b in background_names:
            yield_val = hbackgrounds[b][0].Integral(i + 1, i + 1)
            initial_yield = hbackgrounds[b][0].Integral(1, 1)
            efficiency = (yield_val / initial_yield * 100) if (i > 0 and initial_yield != 0) else 100.0
            # Notice you have parentheses around efficiency here, leaving it as is:
            process_yields[b] = f"{round_to_significant(yield_val)} ({efficiency:.1f})%"

        if total_signal_yield > 0:
            prec_value = 100.0 * np.sqrt(total_signal_yield + total_background_yield) / total_signal_yield
            prec_str = f"{prec_value:.1f}%"
        else:
            prec_str = "inf"

        row = {"Selection Cut": label}
        row.update(process_yields)
        row["prec (\\%)"] = prec_str
        data.append(row)

    df = pd.DataFrame(data)

    # Reorder columns so that 'prec (%)' is last
    cols = list(df.columns)
    if "prec (%)" in cols:
        cols.remove("prec (%)")
        cols.append("prec (%)")
    df = df[cols]

    print(df.to_string(index=False))

    # Apply sanitize_latex only to "Selection Cut" column
    df["Selection Cut"] = df["Selection Cut"].apply(sanitize_latex)

    # Replace '%' with '\%' across the entire DataFrame
    df = df.replace("%", r"\%", regex=True)

    # Wrap the selection cuts in math mode with \rm
    df["Selection Cut"] = df["Selection Cut"].apply(lambda x: f"$\\rm {x}$")

    # create output directory if does not exist
    if not os.path.exists(param.outdir):
        os.makedirs(param.outdir)

    output_table = os.path.join(param.outdir, hist_name + "_cutflow.tex")
    pdf_file = os.path.join(param.outdir, hist_name + "_cutflow.pdf")

    latex_preamble = r"""\documentclass[7pt]{article}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{pdflscape} % add this
\usepackage[margin=1in]{geometry}

\begin{document}
\pagestyle{empty} % No page numbers, headers, or footers
\begin{landscape} % start rotated environment
\small
"""
    latex_postamble = r"""
\end{landscape} % end rotated environment
\end{document}
"""

    table_latex = df.to_latex(index=False, escape=False)
    with open(output_table, "w") as f:
        f.write(latex_preamble)
        f.write(table_latex)
        f.write(latex_postamble)

    pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", param.outdir, output_table]
    os.system("cat " + output_table)
    pdf_generated = False

    try:
        for _ in range(2):
            result = subprocess.run(pdflatex_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if result.returncode != 0:
                print("pdflatex failed to compile the PDF. Output:")
                print(result.stdout.decode("utf-8", errors="ignore"))
                print(result.stderr.decode("utf-8", errors="ignore"))
                break
        if os.path.isfile(pdf_file):
            pdf_generated = True
    except subprocess.TimeoutExpired:
        print("pdflatex timed out. Check if there are infinite loops or problematic packages.")

    if pdf_generated:
        if os.path.isfile(output_table):
            os.remove(output_table)
        base_name = os.path.splitext(os.path.basename(output_table))[0]
        for ext in [".log", ".aux", ".out"]:
            aux_file = os.path.join(param.outdir, base_name + ext)
            if os.path.isfile(aux_file):
                os.remove(aux_file)
    else:
        print("No PDF generated. LaTeX sources are left for debugging.")

    return df


# _____________________________________________________________________________
def drawStack(
    param,
    config,
    name,
    ylabel,
    legend,
    leftText,
    rightText,
    formats,
    directory,
    logY,
    stacksig,
    histos,
    colors,
    ana_tex,
    extralab,
    customLabel,
    nsig,
    nbkg,
    legend2=None,
    yields=None,
    plotStatUnc=False,
    xmin=-1,
    xmax=-1,
    ymin=-1,
    ymax=-1,
    xtitle="",
):
    
    print(" --- processing --- ", name)
    hist_cfg = config["hists"][name]
    doDensity = hist_cfg.get("density", False)
    divideByBinWidth = hist_cfg.get("divideByBinWidth", False)

    systematics = hist_cfg.get("systematics", [])

    print(hist_cfg)
    print(doDensity, divideByBinWidth)
    print(systematics)

    canvas = ROOT.TCanvas(name, name, 800, 800)
    canvas.SetLogy(logY)
    canvas.SetTicks(1, 1)
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.08)

    sumhistos = histos[0].Clone()
    iterh = iter(histos)
    next(iterh)

    unit = "GeV"
    if "TeV" in str(histos[0].GetXaxis().GetTitle()):
        unit = "TeV"

    if unit in str(histos[0].GetXaxis().GetTitle()):
        bwidth = sumhistos.GetBinWidth(1)
        if bwidth.is_integer():
            ylabel += f" / {bwidth} {unit}"
        else:
            ylabel += f" / {bwidth:.2f} {unit}"

    nbins = 1 if not isinstance(xtitle, list) else len(xtitle)
    h_dummy = ROOT.TH1D("h_dummy", "", nbins, 0, nbins)
    if nbins == 1:
        h_dummy.GetXaxis().SetTitle(histos[0].GetXaxis().GetTitle() if xtitle == "" else xtitle)
        h_dummy.GetYaxis().SetTitleOffset(1.95)
        h_dummy.GetXaxis().SetTitleOffset(1.2 * h_dummy.GetXaxis().GetTitleOffset())
    else:  # for cutflow plots
        for i, label in enumerate(xtitle):
            h_dummy.GetXaxis().SetBinLabel(i + 1, label)
        h_dummy.GetXaxis().LabelsOption("u")
        h_dummy.GetXaxis().SetLabelSize(1.1 * h_dummy.GetXaxis().GetLabelSize())
        h_dummy.GetXaxis().SetLabelOffset(1.5 * h_dummy.GetXaxis().GetLabelOffset())
        #h_dummy.GetXaxis().SetRangeUser(-0.5, len(xtitle) - 0.5)
    h_dummy.GetYaxis().SetTitle(ylabel)

    for h in iterh:
        sumhistos.Add(h)

    if logY:
        canvas.SetLogy(1)

    # define stacked histo
    hStack = ROOT.THStack("hstack", "")
    hStackBkg = ROOT.THStack("hstackbkg", "")
    hStackSig = ROOT.THStack("hstacksig", "")
    BgMCHistYieldsDic = {}


    import math
    if len(systematics) > 0:

        syst_dict = {}
        print("Adding systematics")

        empty_bin_indices, merge_index = find_empty_bins(histos[0])

        print(systematics)
        # first calculate the statistical uncertainty (sqrt(Ns+Nb)/Ns)
        print("first calculate the statistical uncertainty (sqrt(Ns+Nb)/Ns)")
        hstat_up = histos[0].Clone()
        hstat_down = histos[0].Clone()  
        for i in range(nsig, nsig + nbkg):
            h = histos[i]

            for j in range(0, h.GetNbinsX()+1):
                print(i, j, hstat_up.GetBinContent(j), hstat_down.GetBinContent(j), h.GetBinContent(j))
                hstat_up.SetBinContent(j, math.sqrt(hstat_up.GetBinContent(j) + h.GetBinContent(j)))
                hstat_up.SetBinError(j, 0.0)
                hstat_down.SetBinContent(j, math.sqrt(hstat_down.GetBinContent(j) + h.GetBinContent(j)))
                hstat_down.SetBinError(j, 0.0)

        hstat_up.Divide(histos[0])
        hstat_down.Divide(hstat_down, histos[0], 1., -1 )

        for i in range(0, hstat_up.GetNbinsX()+1):
            print(f"stat. unc.: [{hstat_up.GetBinLowEdge(i)}, {hstat_up.GetBinLowEdge(i+1)}], bin {i}, up {hstat_up.GetBinContent(i)} down {hstat_down.GetBinContent(i)}")
        
        # now systematics
        for syst in systematics:

            # at least label and type should be defined else skip 
            if "label" not in syst or "type" not in syst:
                LOGGER.error(f"systematic {syst} not defined properly")
                sys.exit(1)

            # supported types are "shape" and "const", if defined differently also skip
            if syst["type"] not in ["shape", "const"]:
                LOGGER.error(f"systematic {syst} type should be 'const' or 'shape'")
                sys.exit(2)

            hsyst_up = histos[0].Clone()
            hsyst_down = histos[0].Clone()
            hsyst_up.Reset()
            hsyst_down.Reset()
            if syst["type"] == "const":

                # then value should be defined
                if "value" not in syst:
                    LOGGER.error(f"systematic {syst} type is const, 'value' should be defined")
                    sys.exit(3)
                
                if syst["signal"]:
                    print (f"Adding signal constant systematic {syst['label']} with value {syst['value']}")
                    for i in range(0, hsyst_up.GetNbinsX()+1):
                        hsyst_up.SetBinContent(i, syst["value"])
                        hsyst_up.SetBinError(i, 0.0)
                        hsyst_down.SetBinContent(i, -syst["value"])
                        hsyst_down.SetBinError(i, 0.0)
                        syst["hist_up"] = hsyst_up
                        syst["hist_down"] = hsyst_down
                        #print(f"Setting systematic {syst['label']} to {syst['value']}")

                else:
                    print (f"Adding background constant systematic {syst['label']} with value {syst['value']}")
                    
                    bkg_name = syst["process"]
                    # find corresponding background index in histos
                    processes = hist_cfg["processes"]
                    idx_bkg = processes.index(bkg_name)
                    print(f"Background index {idx_bkg}")

                    for j in range(1, h.GetNbinsX()+1):
                        Ns = histos[0].GetBinContent(j)
                        Nb = histos[idx_bkg].GetBinContent(j)
                        syst_val = 0
                        if Ns > 0:
                            syst_val = syst["value"] * Nb/Ns
                        else: 
                            print(f"signal is zero in bin {j}, setting systematic {syst['label']} to 0")
                        
                        if abs(syst_val) < 1e-04:
                            syst_val = 1e-04
                        hsyst_up.SetBinContent(j, syst_val)
                        hsyst_up.SetBinError(j, 0.0)
                        hsyst_down.SetBinContent(j, -syst_val)
                        hsyst_down.SetBinError(j, 0.0)
                        print(f"signal {Ns}, background {Nb}")
                        print(f"Setting systematic {syst['label']} to {syst_val}")
                        syst["hist_up"] = hsyst_up
                        syst["hist_down"] = hsyst_down
            
            elif syst["type"] == "shape":
                # first find up and down histograms
                histname_up = f"{hist_cfg['input']}_{syst['hname']}_wp"
                histname_down = f"{hist_cfg['input']}_{syst['hname']}_wm"
                histname = hist_cfg['input']
                
                # create a histogram adding all the histograms of this process
                if "process" not in syst or "signal" not in syst:
                    LOGGER.error(f"systematic {syst} type is shape, 'process' and 'signal' should be defined")
                    sys.exit(4)

                param_call = param
                if not syst["signal"]:
                    import types

                    # Create a new lightweight module
                    param_bkg = types.ModuleType(param.__name__)

                    # Explicitly copy only required attributes
                    for attr in dir(param):
                        # Skip special/private attributes
                        if not attr.startswith("__"):
                            setattr(param_bkg, attr, getattr(param, attr))
                    
                    param_bkg.inputDir = syst["path"]
                    param_call = param_bkg
                
                hsignal_up, hbackgrounds_up = mapHistosFromHistmaker(config, histname_up, param_call, hist_cfg)
                hsignal_down, hbackgrounds_down = mapHistosFromHistmaker(config, histname_down, param_call, hist_cfg)
                hsignal, hbackgrounds = mapHistosFromHistmaker(config, histname, param_call, hist_cfg)

                print(hsignal_up, hbackgrounds_up)

                if len(hsignal_up) != nsig:
                    LOGGER.error(f"somethings is strange with the systematic {syst['label']}, signal histograms are not correct")
                    sys.exit(4)
                
                if nsig != 1:
                    LOGGER.error(f"systematic {syst['label']} is shape, only one signal process is supported")
                    sys.exit(5)

                sample_up = hsignal_up
                sample_down = hsignal_down
                sample = hsignal
                
                # hist1 = histos[0]
                # hist2 = sample[syst["process"]][0]
                # if hist1.GetNbinsX() != hist2.GetNbinsX():
                #     print("Histograms have different binning!")
                #     return

                # print(f"{'Bin':>5} | {'Hist1':>12} | {'Hist2':>12} | {'Diff':>12}")
                # print("-" * 50)
    
                # for bin_idx in range(1, hist1.GetNbinsX() + 1):
                #     val1 = hist1.GetBinContent(bin_idx)
                #     val2 = hist2.GetBinContent(bin_idx)/hist2.GetBinWidth(bin_idx)
                #     diff = val1 - val2
                #     print(f"{bin_idx:5} | {val1:12.4f} | {val2:12.4f} | {diff:12.4f}")
                
                if not syst["signal"]:
                    sample_up = hbackgrounds_up
                    sample_down = hbackgrounds_down
                    sample = hbackgrounds
                    
                if syst["process"] in sample_up:
                    hsyst_up = sample_up[syst["process"]][0].Clone()
                    hsyst_down = sample_down[syst["process"]][0].Clone()
                    hsyst_nominal = sample[syst["process"]][0].Clone()

                    hsyst_up = rebin_last_empty_bins(hsyst_up, empty_bin_indices, merge_index)
                    hsyst_down = rebin_last_empty_bins(hsyst_down, empty_bin_indices, merge_index)
                    hsyst_nominal = rebin_last_empty_bins(hsyst_nominal, empty_bin_indices, merge_index)

                    for i in range(0, hsyst_up.GetNbinsX()+1):
                        # print(f"systematic {syst['label']} bin {i} up {hsyst_up.GetBinContent(i)} down {hsyst_down.GetBinContent(i)} nominal {hsyst_nominal.GetBinContent(i)}, bin width {hsyst_up.GetBinWidth(i)}")

                        syst_up = 0.
                        syst_down = 0.
                        if histos[0].GetBinContent(i) > 0:

                            syst_up = (hsyst_up.GetBinContent(i) - hsyst_nominal.GetBinContent(i))/histos[0].GetBinContent(i)
                            syst_down = (hsyst_down.GetBinContent(i) - hsyst_nominal.GetBinContent(i))/histos[0].GetBinContent(i)
                                  
                            print(f"systematic {syst['label']}, [{hsyst_up.GetBinLowEdge(i)}, {hsyst_up.GetBinLowEdge(i+1)}],  bin {i} up {syst_up} down {syst_down}")
                            
                            # if not signal add stat. uncertainty from CR
                            if not syst["signal"]:

                                # if hsyst_nominal.GetBinContent(i) == 0 , pick value from last no empty bin
                                # if hsyst_nominal.GetBinContent(i) == 0:
                                #     for j in range(i, 0, -1):
                                #         if hsyst_nominal.GetBinContent(j) != 0:
                                #             hsyst_nominal.SetBinContent(i, hsyst_nominal.GetBinContent(j))
                                #             break

                                if hsyst_nominal.GetBinContent(i) > 0:
                                    bkg_stat_unc = 1./math.sqrt(hsyst_nominal.GetBinContent(i))
                                else:
                                    bkg_stat_unc = 0

                                print(f" stat. uncertainty from CR {bkg_stat_unc}")

                                # this dNb/Nb in SR
                                syst_up = math.sqrt(syst_up**2 + bkg_stat_unc**2)
                                syst_down = -math.sqrt(syst_down**2 + bkg_stat_unc**2)
                                Ns = histos[0].GetBinContent(i)
                                Nb = hsyst_nominal.GetBinContent(i)

                                print(f" stat. uncertainty from CR {bkg_stat_unc} Ns {Ns} Nb {Nb}")
                               
                                # now normalise to to actual uncertainty on signal i.e. (dNb/Nb) * Nb/Ns
                                syst_up = syst_up * Nb/Ns
                                syst_down = syst_down * Nb/Ns

                                print(f" stat. uncertainty from CR {bkg_stat_unc} Ns {Ns} Nb {Nb} syst_up {syst_up} syst_down {syst_down}")



                        hsyst_up.SetBinContent(i, syst_up)   
                        hsyst_down.SetBinContent(i, syst_down)
                        hsyst_up.SetBinError(i, 0.0)
                        hsyst_down.SetBinError(i, 0.0)

                    syst["hist_up"] = hsyst_up
                    syst["hist_down"] = hsyst_down
        

        hsyst_total_up = histos[0].Clone()
        hsyst_total_down = histos[0].Clone()
        hsyst_total_down.Reset()
        hsyst_total_up.Reset()
        for syst in systematics:
            if "hist_up" in syst and "hist_down" in syst:
                for i in range(0, hsyst_total_up.GetNbinsX()+1):
                    hsyst_total_up.SetBinContent(i, math.sqrt(hsyst_total_up.GetBinContent(i)**2 + syst["hist_up"].GetBinContent(i)**2))
                    hsyst_total_down.SetBinContent(i, -math.sqrt(hsyst_total_down.GetBinContent(i)**2 + syst["hist_down"].GetBinContent(i)**2))
                    hsyst_total_up.SetBinError(i, 0.0)
                    hsyst_total_down.SetBinError(i, 0.0)

        # now compute total uncertainty stat+syst
        h_unc_total_up = hsyst_total_up.Clone()
        h_unc_total_down = hsyst_total_down.Clone()
        h_unc_total_up.Reset()
        h_unc_total_down.Reset()
        for i in range(0, h_unc_total_up.GetNbinsX()+1):
            h_unc_total_up.SetBinContent(i, math.sqrt(hsyst_total_up.GetBinContent(i)**2 + hstat_up.GetBinContent(i)**2))
            h_unc_total_down.SetBinContent(i, -math.sqrt(hsyst_total_down.GetBinContent(i)**2 + hstat_down.GetBinContent(i)**2))
            h_unc_total_up.SetBinError(i, 0.0)
            h_unc_total_down.SetBinError(i, 0.0)


        print("")
        print("------------------------------------------------")
        print("observable: {}".format(histos[0].GetName()))
        print("------------------------------------------------")

        # Collect your data into a list of dictionaries
        data = []
        # Loop through bins (assuming bins are indexed from 1 to N)
        for bin_idx in range(1, h_unc_total_up.GetNbinsX() + 1):

            bin_data = {
                "bin_min": f"{h_unc_total_up.GetBinLowEdge(bin_idx):.2f}",
                "bin_max": f"{h_unc_total_up.GetBinLowEdge(bin_idx + 1):.2f}",
                "nsig": f"{histos[0].GetBinContent(bin_idx):.0f}",
            }

            nb_total = 0
            # Use a different variable (hist_idx) for the inner loop
            for hist_idx in range(nsig, nsig + nbkg):
                h = histos[hist_idx]
                nb_total += h.GetBinContent(bin_idx)

            bin_data["nbkg"] = f"{nb_total:.0f}"

            for syst in systematics:
                bin_data[f"rel_syst_{syst['label']}"] = f"{syst['hist_up'].GetBinContent(bin_idx):.3f}"

            bin_data["rel_stat"] = f"{hstat_up.GetBinContent(bin_idx):.3f}"
            bin_data["rel_syst_tot"] = f"{hsyst_total_up.GetBinContent(bin_idx):.3f}"
            bin_data["rel_unc_total"] = f"{h_unc_total_up.GetBinContent(bin_idx):.3f}"

            data.append(bin_data)

        # Create a DataFrame from the collected data
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
        print("")
        print("")

        if hist_cfg.get("store_csv", False):
            df.to_csv(os.path.join(directory, f"{name}_uncertainties.csv"), index=False)


    # if divibyBinWidth defined, divide all histogram bin content by bin width, and set error accordingly
    if divideByBinWidth:
        for h in histos:
            for i in range(1, h.GetNbinsX()+1):
                # print bin boundaries
                # print(f"[{h.GetBinLowEdge(i)}, {h.GetBinLowEdge(i+1)}]")
                # print("content, error, width: ", h.GetBinContent(i), h.GetBinError(i), h.GetBinWidth(i))
                h.SetBinContent(i, h.GetBinContent(i) / h.GetBinWidth(i))
                h.SetBinError(i, h.GetBinError(i) / h.GetBinWidth(i))


    # first plot backgrounds (sorted by the yields)
    for i in range(nsig, nsig + nbkg):
        h = histos[i]
        h.SetLineWidth(1)
        h.SetLineColor(ROOT.kBlack)
        h.SetFillColor(colors[i])
        if h.Integral() > 0:
            BgMCHistYieldsDic[h.Integral()] = h
        else:
            BgMCHistYieldsDic[-1 * nbkg] = h
    # sort stack by yields (smallest to largest)
    BgMCHistYieldsDic = sorted_dict_values(BgMCHistYieldsDic)
    for h in BgMCHistYieldsDic:
        hStack.Add(h)
        hStackBkg.Add(h)

    # add the signal histograms
    for i in range(nsig):
        h = histos[i]
        h.SetLineWidth(3)
        h.SetLineColor(colors[i])
        h.SetMarkerColor(colors[i])
        hStack.Add(h)
        hStackSig.Add(h)

    if xmin != -1 and xmax != -1:
        h_dummy.GetXaxis().SetLimits(xmin, xmax)

    h_dummy.Draw("HIST")
    if doDensity:
        for h in histos:
            h.Scale(1.0 / h.Integral(0, h.GetNbinsX()+1))
            h.Draw("HIST SAME")

    elif stacksig:
        hStack.Draw("HIST SAME")
        if plotStatUnc:
            # sig+bkg uncertainty
            hUnc_sig_bkg = formatStatUncHist(hStack.GetHists(), "sig_bkg")
            hUnc_sig_bkg.Draw("E2 SAME")
    else:
        if len(systematics) > 0:
            # Plotting the ratio
            hNumerator = hStackBkg.GetStack().Last().Clone("hNumerator")

            ROOT.gStyle.SetOptStat(0)  # remove stat box

            canvas = ROOT.TCanvas("c", "", 800, 800)

            upper_pad = ROOT.TPad("upper_pad", "", 0, 0.35, 1, 1.0)
            lower_pad = ROOT.TPad("lower_pad", "", 0, 0.0, 1, 0.35)

            upper_pad.SetBottomMargin(0.02)
            upper_pad.SetLeftMargin(0.14)
            lower_pad.SetLeftMargin(0.14)
            lower_pad.SetTopMargin(0.05)
            lower_pad.SetBottomMargin(0.3)

            upper_pad.Draw()
            lower_pad.Draw()

            upper_pad.cd()
            upper_pad.SetLogy(True)

            # Create a dummy histogram to set the axis ranges
            # Here we clone the last histogram from the stack and reset it.
            h_dummy_upper = hStackBkg.GetStack().Last().Clone("h_dummy_upper")
            h_dummy_upper.Reset()  # remove all content
            h_dummy_upper.GetXaxis().SetLimits(xmin, xmax)  # set x-axis limits
            h_dummy_upper.GetXaxis().SetRangeUser(xmin, xmax)  # set x-axis limits
            h_dummy_upper.SetMinimum(ymin)  # set y-axis minimum
            h_dummy_upper.SetMaximum(ymax)  # set y-axis maximum

            h_dummy_upper.GetYaxis().SetTitle(ylabel)
            h_dummy_upper.GetXaxis().SetLabelSize(0)
            h_dummy_upper.GetXaxis().SetTitleSize(0)
            h_dummy_upper.GetYaxis().SetTitleSize(0.05)
            h_dummy_upper.GetYaxis().SetLabelSize(0.05)
            h_dummy_upper.GetYaxis().SetTitleOffset(1.3)

            # Draw the dummy histogram's axes
            h_dummy_upper.Draw("AXIS")

            # Check background stack contents explicitly
            h_background_total = hStackBkg.GetStack().Last()
            min_bkg_bin = min(h_background_total.GetBinContent(i) for i in range(1, h_background_total.GetNbinsX()+1))
            print("Min bin content in background histogram stack:", min_bkg_bin)

            # Check signal stack explicitly
            h_signal_total = hStackSig.GetStack().Last()
            min_sig_bin = min(h_signal_total.GetBinContent(i) for i in range(1, h_signal_total.GetNbinsX()+1))
            print("Min bin content in signal histogram stack:", min_sig_bin)

            # Now draw your stack histograms on top
            hStackBkg.Draw("HIST SAME")
            hStackSig.Draw("HIST SAME NOSTACK")

            # Draw the dummy histogram's axes
            h_dummy_upper.Draw("AXIS SAME")

            lower_pad.cd()

            # Draw a frame with the desired x-axis limits.
            # Here, for example, we assume your ratio range is [-1, 1]—adjust as needed.
            # frame = lower_pad.DrawFrame(xmin, -1, xmax, 1)
            # frame.GetXaxis().SetTitle(xtitle)
            # frame.GetYaxis().SetTitle("uncertainty [%]")
            # frame.GetYaxis().SetRangeUser(-1, 1)  # or whatever range you need

            # Activate ticks on all sides
            lower_pad.SetTicks(1, 1)

            # Enable grids for major and minor ticks
            lower_pad.SetGridx(True)
            lower_pad.SetGridy(True)

            # Activate minor ticks/grid lines explicitly
            lower_pad.SetLogy(False) 

            legend_ind = ROOT.TLegend(0.45, 0.92 - len(systematics)*0.045, 0.85, 0.92)
            # legend_ind.SetBorderSize(0)
            legend_ind.SetFillStyle(1001)
            legend_ind.SetFillColor(0)
            legend_ind.SetTextSize(0.05)

            for i, syst in enumerate(systematics):
                for var in ["up", "down"]:
                    print(f"plotting systematic {syst['label']} {var}")
                    bottom = syst[f"hist_{var}"]

                    def check_same_binning(h1, h2):
                        if h1.GetNbinsX() != h2.GetNbinsX():
                            return False
                        for i in range(1, h1.GetNbinsX() + 2):
                            print(i, h1.GetBinLowEdge(i), h2.GetBinLowEdge(i), h1.GetBinContent(i), h2.GetBinContent(i))
                            if h1.GetBinLowEdge(i) != h2.GetBinLowEdge(i):
                                return False
                        return True

                    if not check_same_binning(hNumerator, bottom):
                        print("Binning of the histograms is not consistent. Exiting.")

                    bottom.SetMarkerStyle(20)
                    bottom.SetMarkerSize(0.)
                    bottom.SetLineColor(syst["color"])
                    bottom.SetLineWidth(2)
                    bottom.SetFillColor(0)
                    bottom.SetTitle(xtitle)


                    if i == 0 and var == "up":
                        bottom.Draw("HIST")
                        #bottom.GetYaxis().SetRangeUser(-1, 1)
                        bottom.GetYaxis().SetRangeUser(-0.2, 0.2)
                        if "yrange_syst" in hist_cfg:
                            bottom.GetYaxis().SetRangeUser(hist_cfg["yrange_syst"][0], hist_cfg["yrange_syst"][1])
                        bottom.GetXaxis().SetLimits(xmin, xmax)  # set x-axis limits
                        bottom.GetXaxis().SetRangeUser(xmin, xmax)
                        bottom.GetYaxis().SetTitle("uncertainty")
                        bottom.GetXaxis().SetTitle(xtitle)
                        bottom.GetYaxis().SetNdivisions(505, True)

                        bottom.GetYaxis().SetTitleSize(0.09)
                        bottom.GetYaxis().SetLabelSize(0.09)
                        bottom.GetYaxis().SetTitleOffset(0.66)

                        bottom.GetXaxis().SetTitleSize(0.11)
                        bottom.GetXaxis().SetLabelSize(0.09)
                        bottom.GetXaxis().SetTitleOffset(0.9)
                    else:    
                        bottom.Draw("hist same")

                legend_ind.AddEntry(bottom, syst["label"], "l")

            hstat_down.SetMarkerSize(0.)
            hstat_down.SetMarkerColor(ROOT.kGray+1)
            hstat_down.SetLineColor(ROOT.kGray+1)
            hstat_down.SetLineWidth(2)
            hstat_down.SetLineStyle(2)
            hstat_down.SetFillColor(0)
            hstat_down.Draw("hist same")

            hstat_up.SetMarkerSize(0.)
            hstat_up.SetMarkerColor(ROOT.kGray+1)
            hstat_up.SetLineColor(ROOT.kGray+1)
            hstat_up.SetLineWidth(2)
            hstat_up.SetLineStyle(2)
            hstat_up.SetFillColor(0)
            hstat_up.Draw("hist same")

            hsyst_total_down.SetMarkerStyle(20)
            hsyst_total_down.SetMarkerSize(0.)
            hsyst_total_down.SetLineColor(ROOT.kGray+1)
            hsyst_total_down.SetLineWidth(2)
            hsyst_total_down.SetLineStyle(1)
            hsyst_total_down.SetFillColor(0)
            
            
            hsyst_total_up.SetMarkerStyle(20)
            hsyst_total_up.SetMarkerSize(0.)
            hsyst_total_up.SetLineColor(ROOT.kGray+1)
            hsyst_total_up.SetLineWidth(3)
            hsyst_total_up.SetLineStyle(1)
            hsyst_total_up.SetFillColor(0)
            hsyst_total_down.Draw("hist same")
            hsyst_total_up.Draw("hist same")

            h_unc_total_down.SetMarkerStyle(20)
            h_unc_total_down.SetMarkerSize(0.)
            h_unc_total_down.SetLineColor(ROOT.kBlack)
            h_unc_total_down.SetLineWidth(2)
            h_unc_total_down.SetLineStyle(1)
            h_unc_total_down.SetFillColor(0)

            
            h_unc_total_up.SetMarkerStyle(20)
            h_unc_total_up.SetMarkerSize(0.)
            h_unc_total_up.SetLineColor(ROOT.kBlack)
            h_unc_total_up.SetLineWidth(2)
            h_unc_total_up.SetLineStyle(1)
            h_unc_total_up.SetFillColor(0)
            h_unc_total_down.Draw("hist same")
            h_unc_total_up.Draw("hist same")


            legend_syst = ROOT.TLegend(0.70, 0.75, 0.85, 0.92)
            legend_ind.SetFillStyle(1001)
            legend_ind.SetFillColor(0)
            legend_ind.SetTextSize(0.05)

            legend_syst.AddEntry(hstat_down, "stat.", "l")
            legend_syst.AddEntry(hsyst_total_down, "syst.", "l")
            legend_syst.AddEntry(h_unc_total_down, "stat + syst", "l")

            legend_ind.Draw()
            legend_syst.Draw()

            upper_pad.cd()
            upper_pad.Modified()
            upper_pad.Update()

            canvas.Modified()
            canvas.Update()

            print_canvas(canvas, name, formats, directory)

        else:
            hStackBkg.Draw("HIST SAME")
            hStackSig.Draw("HIST SAME NOSTACK")

        if plotStatUnc:
            # bkg-only uncertainty
            if hStackBkg.GetNhists() != 0:
                hUnc_bkg = formatStatUncHist(hStackBkg.GetHists(), "bkg_only")
                hUnc_bkg.Draw("E2 SAME")
            for sHist in hStackSig.GetHists():
                # sigs uncertainty
                hUnc_sig = formatStatUncHist([sHist], "sig", 3245)
                hUnc_sig.Draw("E2 SAME")

    # x limits
    if xmin == -1:
        h_tmp = hStack.GetStack().Last()
        xmin = h_tmp.GetBinLowEdge(1)
    if xmax == -1:
        h_tmp = hStack.GetStack().Last()
        xmax = h_tmp.GetBinLowEdge(h_tmp.GetNbinsX() + 1)

    h_dummy.GetXaxis().SetLimits(xmin, xmax)

    # if cutFlow table
    if isinstance(xtitle, list):
        h_dummy.GetXaxis().SetLimits(-0.5, len(xtitle) - 0.5)

    # y limits
    def get_minmax_range(hists, xmin, xmax):
        hist_tot = hists[0].Clone(name + "_unc")
        for h in hists[1:]:
            hist_tot.Add(h)
        vals = []
        for i in range(0, hist_tot.GetNbinsX() + 1):
            if hist_tot.GetBinLowEdge(i) > xmin or hist_tot.GetBinLowEdge(i + 1) < xmax:
                if hist_tot.GetBinContent(i) != 0:
                    vals.append(hist_tot.GetBinContent(i))
        if len(vals) == 0:
            return 1e-5, 1
        return min(vals), max(vals)

    if stacksig:
        ymin_, ymax_ = get_minmax_range(hStack.GetHists(), xmin, xmax)
    else:
        if hStackSig.GetNhists() != 0 and hStackBkg.GetNhists() != 0:
            ymin_sig, ymax_sig = get_minmax_range(hStackSig.GetHists(), xmin, xmax)
            ymin_bkg, ymax_bkg = get_minmax_range(hStackBkg.GetHists(), xmin, xmax)
            ymin_ = min(ymin_sig, ymin_bkg)
            ymax_ = max(ymax_sig, ymax_bkg)
        elif hStackSig.GetNhists() == 0:
            ymin_, ymax_ = get_minmax_range(hStackBkg.GetHists(), xmin, xmax)
        elif hStackBkg.GetNhists() == 0:
            ymin_, ymax_ = get_minmax_range(hStackSig.GetHists(), xmin, xmax)
    if ymin == -1:
        ymin = ymin_ * 0.1 if logY else 0
    if ymax == -1:
        ymax = ymax_ * 1000.0 if logY else 1.4 * ymax_
    if ymin <= 0 and logY:
        LOGGER.error("Log scale can't start at: %i", ymin)
        sys.exit(3)

    if len(systematics) == 0:
        h_dummy.SetMaximum(ymax)
        h_dummy.SetMinimum(ymin)

    legend.Draw()
    if legend2 is not None:
        legend2.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAlign(11)
    latex.SetTextSize(0.03)

    xpos = 0.15
    ypos = 0.91
    if len(systematics) > 0:
        latex.SetTextSize(0.045)
        xpos = 0.14

    text = leftText
    latex.DrawLatex(xpos, ypos, text)

    latex.SetTextAlign(31)
    latex.SetTextSize(0.03)

    text = "#bf{" + rightText + "}"

    if len(systematics) > 0:
        latex.SetTextSize(0.045)
 
    latex.DrawLatex(0.90, 0.91, text)



    text = "#it{" + customLabel + "}"
    latex.SetTextAlign(12)
    latex.SetNDC(ROOT.kTRUE)
    latex.SetTextSize(0.04)
    latex.DrawLatex(0.18, 0.85, text)

    rightText = re.split(",", rightText)
    text = "#bf{#it{" + rightText[0] + "}}"

    latex.SetTextAlign(12)
    latex.SetNDC(ROOT.kTRUE)
    latex.SetTextSize(0.04)
    # latex.DrawLatex(0.18, 0.81, text)

    rightText[1] = rightText[1].replace("   ", "")
    text = "#bf{#it{" + rightText[1] + "}}"
    latex.SetTextSize(0.035)
    # latex.DrawLatex(0.18, 0.76, text)

    text = "#bf{" + ana_tex + "}"
    latex.SetTextSize(0.035)
    latex.DrawLatex(0.20, 0.83, text)

    text = "#bf{#it{" + extralab + "}}"
    latex.SetTextSize(0.025)
    latex.DrawLatex(0.18, 0.66, text)

    if config["scale_sig"] != 1.0:
        text = "#bf{#it{Signal Scaling = " + f'{config["scale_sig"]:.3g}' + "}}"
        latex.SetTextSize(0.025)
        latex.DrawLatex(0.18, 0.63, text)

    if config["scale_bkg"] != 1.0:
        text = "#bf{#it{Background Scaling = " + f'{config["scale_bkg"]:.3g}' + "}}"
        latex.SetTextSize(0.025)
        latex.DrawLatex(0.18, 0.63, text)


    canvas.RedrawAxis()
    canvas.GetFrame().SetBorderSize(12)
    canvas.Modified()
    canvas.Update()

    if "AAAyields" in name:
        dummyh = ROOT.TH1F("", "", 1, 0, 1)
        dummyh.SetStats(0)
        dummyh.GetXaxis().SetLabelOffset(999)
        dummyh.GetXaxis().SetLabelSize(0)
        dummyh.GetYaxis().SetLabelOffset(999)
        dummyh.GetYaxis().SetLabelSize(0)
        dummyh.Draw("AH")
        legend.Draw()

        latex.SetNDC()
        latex.SetTextAlign(31)
        latex.SetTextSize(0.04)

        text = "#it{" + leftText + "}"
        latex.DrawLatex(0.90, 0.92, text)

        text = "#bf{#it{" + rightText[0] + "}}"
        latex.SetTextAlign(12)
        latex.SetNDC(ROOT.kTRUE)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.18, 0.83, text)

        text = "#bf{#it{" + rightText[1] + "}}"
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.18, 0.78, text)

        text = "#bf{#it{" + ana_tex + "}}"
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.18, 0.73, text)

        text = "#bf{#it{" + extralab + "}}"
        latex.SetTextSize(0.025)
        latex.DrawLatex(0.18, 0.68, text)

        text = "#bf{#it{Signal Scaling = " + f'{config["scale_sig"]:.3g}' + "}}"
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.18, 0.57, text)

        text = "#bf{#it{Background Scaling = " + f'{config["scale_bkg"]:.3g}' + "}}"
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.18, 0.52, text)

        dy = 0
        text = "#bf{#it{" + "Process" + "}}"
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.18, 0.45, text)

        text = "#bf{#it{" + "Yields" + "}}"
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.5, 0.45, text)

        text = "#bf{#it{" + "Raw MC" + "}}"
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.75, 0.45, text)

        for y in yields:
            text = "#bf{#it{" + yields[y][0] + "}}"
            latex.SetTextSize(0.035)
            latex.DrawLatex(0.18, 0.4 - dy * 0.05, text)

            stry = str(yields[y][1])
            stry = stry.split(".", maxsplit=1)[0]
            text = "#bf{#it{" + stry + "}}"
            latex.SetTextSize(0.035)
            latex.DrawLatex(0.5, 0.4 - dy * 0.05, text)

            stry = str(yields[y][2])
            stry = stry.split(".", maxsplit=1)[0]
            text = "#bf{#it{" + stry + "}}"
            latex.SetTextSize(0.035)
            latex.DrawLatex(0.75, 0.4 - dy * 0.05, text)

            dy += 1
        # canvas.Modified()
        # canvas.Update()

    print_canvas(canvas, name, formats, directory)


# _____________________________________________________________________________
def print_canvas(canvas, name, formats, directory):
    """
    Saving canvas in multiple formats.
    """

    if not formats:
        LOGGER.error("No output formats specified!\nAborting...")
        sys.exit(3)

    if not os.path.exists(directory):
        os.system("mkdir -p " + directory)

    for f in formats:
        out_file = os.path.join(directory, name) + "." + f
        canvas.SaveAs(out_file)


# _____________________________________________________________________________
def run(args):
    """
    Run over all the plots.
    """
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning

    module_path = os.path.abspath(args.script_path)
    module_dir = os.path.dirname(module_path)
    base_name = os.path.splitext(ntpath.basename(args.script_path))[0]

    # Load plot script as module
    sys.path.insert(0, module_dir)
    script_module = importlib.import_module(base_name)

    # Merge script and command line arguments into one configuration object
    # Also check the script attributes
    config: dict[str, any] = {}

    # Input directory
    config["input_dir"] = os.getcwd()
    if hasattr(script_module, "indir"):
        config["input_dir"] = script_module.indir
    if hasattr(script_module, "inputDir"):
        config["input_dir"] = script_module.inputDir
    if args.input_dir is not None:
        config["input_dir"] = args.input_dir

    # Output directory
    config["output_dir"] = os.getcwd()
    if hasattr(script_module, "outdir"):
        config["output_dir"] = script_module.outdir
    if hasattr(script_module, "outputDir"):
        config["output_dir"] = script_module.outputDir
    if args.output_dir is not None:
        config["output_dir"] = args.output_dir

    # Integrated luminosity
    config["int_lumi"] = 1.0
    if hasattr(script_module, "intLumi"):
        config["int_lumi"] = script_module.intLumi
    else:
        LOGGER.debug("No integrated luminosity provided, using 1.0 pb-1.")
    LOGGER.info("Integrated luminosity: %g pb-1", config["int_lumi"])

    # Whether to scale histograms to luminosity
    config["do_scale"] = 1.0
    if hasattr(script_module, "doScale"):
        config["do_scale"] = script_module.doScale
    else:
        LOGGER.debug("No scaling to luminosity requested, scaling won't be " "done.")
        config["do_scale"] = False
    if config["do_scale"]:
        LOGGER.info("Histograms will be scaled to luminosity.")

    # Scale factor to apply to all signal histograms
    config["scale_sig"] = 1.0
    if hasattr(script_module, "scaleSig"):
        config["scale_sig"] = script_module.scaleSig
    else:
        LOGGER.debug("No scale factor for signal provided, using 1.0.")
    LOGGER.info("Scale factor for signal: %g", config["scale_sig"])

    # Scale factor to apply to all background histograms
    config["scale_bkg"] = 1.0
    if hasattr(script_module, "scaleBkg"):
        config["scale_bkg"] = script_module.scaleBkg
    else:
        LOGGER.debug("No scale factor for background provided, using 1.0.")
    LOGGER.info("Scale factor for background: %g", config["scale_sig"])

    # Check if we have plots (staged analysis) or histos (histmaker)
    config["plots"]: dict[str, any] = {}
    config["hists"]: dict[str, any] = {}
    config["ana_type"]: str = "none"
    if hasattr(script_module, "plots"):
        config["plots"] = script_module.plots
        config["ana_type"]: str = "staged"
    if hasattr(script_module, "hists"):
        config["hists"] = script_module.hists
        config["ana_type"]: str = "histmaker"

    if config["ana_type"] == "none":
        LOGGER.error("No plot definitions found!\nAborting...")
        sys.exit(3)

    # Splitting legend into two columns
    config["split_leg"] = False
    if hasattr(script_module, "splitLeg"):
        config["split_leg"] = script_module.splitLeg

    config["leg_position"] = [None, None, None, None]
    if hasattr(script_module, "legendCoord"):
        config["leg_position"] = script_module.legendCoord
    if args.legend_x_min is not None:
        config["leg_position"][0] = args.legend_x_min
    if args.legend_y_min is not None:
        config["leg_position"][1] = args.legend_y_min
    if args.legend_x_max is not None:
        config["leg_position"][2] = args.legend_x_max
    if args.legend_y_max is not None:
        config["leg_position"][3] = args.legend_y_max

    config["plot_stat_unc"] = False
    if hasattr(script_module, "plotStatUnc"):
        config["plot_stat_unc"] = script_module.plotStatUnc

    config["legend_text_size"] = 0.035
    if hasattr(script_module, "legendTextSize"):
        config["legend_text_size"] = script_module.legendTextSize
    if args.legend_text_size is not None:
        config["legend_text_size"] = args.legend_text_size

    # Label for the integrated luminosity
    config["int_lumi_label"] = None
    if hasattr(script_module, "intLumiLabel"):
        config["int_lumi_label"] = script_module.intLumiLabel
    if config["int_lumi_label"] is None:
        if config["int_lumi"] >= 1e6:
            int_lumi_label = config["int_lumi"] / 1e6
            config["int_lumi_label"] = f"L = {int_lumi_label:.2g} ab^{{-1}}"
        elif config["int_lumi"] >= 1e3:
            int_lumi_label = config["int_lumi"] / 1e3
            config["int_lumi_label"] = f"L = {int_lumi_label:.2g} fb^{{-1}}"
        else:
            config["int_lumi_label"] = f'L = {config["int_lumi"]:.2g} pb^{{-1}}'

    # Handle plots for the Histmaker analyses and exit
    if config["ana_type"] == "histmaker":
        LOGGER.info("Plotting histograms from histmaker step...")
        for hist_name, hist_cfg in script_module.hists.items():
            runPlotsHistmaker(config, args, hist_cfg["input"], script_module, hist_cfg)
        for hist_name, hist_cfg in script_module.hists2D.items():
            runPlotsHistmaker2D(config, args, hist_cfg["input"], script_module, hist_cfg)
        sys.exit()

    counter = 0
    LOGGER.info("Plotting staged analysis plots...")
    for var_index, var in enumerate(script_module.variables):
        for label, sels in script_module.selections.items():
            for sel in sels:
                rebin_tmp = 1
                if hasattr(script_module, "rebin"):
                    if len(script_module.rebin) == len(script_module.variables):
                        rebin_tmp = script_module.rebin[var_index]

                LOGGER.info("  var: %s     label: %s     selection: %s", var, label, sel)

                hsignal, hbackgrounds = load_hists(var, label, sel, config, rebin=rebin_tmp)
                runPlots(
                    config,
                    args,
                    var + "_" + label,
                    sel,
                    script_module,
                    hsignal,
                    hbackgrounds,
                    script_module.extralabel[sel],
                )
                if counter == 0:
                    runPlots(
                        config,
                        args,
                        "AAAyields_" + label,
                        sel,
                        script_module,
                        hsignal,
                        hbackgrounds,
                        script_module.extralabel[sel],
                    )
        counter += 1


def do_plots(parser):
    """
    Run plots generation
    """

    args, _ = parser.parse_known_args()

    if args.command != "plots":
        LOGGER.error("Wrong sub-command!\nAborting...")

    if not os.path.isfile(args.script_path):
        LOGGER.error('Plots script "%s" not found!\nAborting...', args.script_path)
        sys.exit(3)

    run(args)

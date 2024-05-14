# This scripts contains some common utility functions for the Gas Cost Estimator
# project `.Rmd` scripts

library(sqldf)
library(nlme)
library(mixtools)
library(zeallot) # for multi-assignment %<-%

# prevent scientific notation
options(scipen = 100)


load_data_set_from_file <- function(filepath) {
  result = read.csv(filepath)
  result$env = env
  if (!('measure_total_time_ns' %in% colnames(result))) {
    if ('total_time_ns' %in% colnames(result)) {
      result$measure_total_time_ns = result$total_time_ns
    }
  }
  if (!('measure_total_timer_time_ns' %in% colnames(result))) {
    if ('engine_overhead_time_ns' %in% colnames(result)) {
      result$measure_total_timer_time_ns = result$engine_overhead_time_ns
    }
  }
  return(result)
}

load_data_set <- function(env, program_set_codename, measurement_codename) {
  data_set_codename = paste(program_set_codename, "_", measurement_codename, sep="")
  filepath = paste("../../local/", env, "_", data_set_codename, ".csv", sep="")
  return (load_data_set_from_file(filepath))
}

remove_outliers <- function(df, col, for_validation) {
  if (missing(for_validation)) {
    for_validation = FALSE
  }
  if (for_validation) {
    boxplot_result = boxplot(df[, col] ~ df[, 'program_id'] + df[, 'env'], plot=FALSE)
  } else {
    boxplot_result = boxplot(df[, col] ~ df[, 'op_count'] + df[, 'env'] + df[, 'opcode'], plot=FALSE)
  }
  outliers = boxplot_result$out
  names = boxplot_result$names[boxplot_result$group]
  if (for_validation) {
    all_row_identifiers = paste(df[, col], df[, 'program_id'], df[, 'env'], sep='.')
  } else {
    all_row_identifiers = paste(df[, col], df[, 'op_count'], df[, 'env'], df[, 'opcode'], sep='.')
  }
  outlier_row_identifiers = paste(outliers, names, sep='.')
  no_outliers = df[-which(all_row_identifiers %in% outlier_row_identifiers), ]
  return(no_outliers)
}

remove_compare_outliers <- function(df, col, all_envs, for_validation) {
  if (missing(for_validation)) {
    for_validation = FALSE
  }
  if (for_validation) {
    category_col = 'program_id'
  } else {
    category_col = 'opcode'
  }
  par(mfrow=c(length(all_envs)*2, 1))
  # before
  for (env in all_envs) {
    boxplot(df[which(df$env == env), col] ~ df[which(df$env == env), category_col], las=2, outline=TRUE, log='y', main=paste(env, 'all'))
  }
  no_outliers = remove_outliers(df=df, col=col, for_validation=for_validation)
  # after
  for (env in all_envs) {
    boxplot(no_outliers[which(no_outliers$env == env), col] ~ no_outliers[which(no_outliers$env == env), category_col], las=2, outline=TRUE, log='y', main=paste(env, 'no_outliers'))
  }
  return(no_outliers)
}

geth_color = rgb(0.1,0.1,0.7,0.5)
evmone_color = rgb(0.8,0.1,0.3,0.6)
besu_color = rgb(0.5,0.1,0.5,0.4)
nethermind_color = rgb(0.4,0.2,0.6,0.8)
ethereumjs_color = rgb(0.3,0.8,0.2,0.6)
erigon_color = rgb(0.8,0.8,0.1,0.7)
revm_color = rgb(0.2,0.7,0.8,0.3)

env_colors = c(geth_color, evmone_color, besu_color, nethermind_color, ethereumjs_color, erigon_color, revm_color)

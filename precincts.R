# Libraries
library(dplyr)
library(readr)
library(stringr)
library(magrittr)


#-------------------
# Useful functions
#-------------------
# Crudely capitalize the first letter in every word
title.case <- function(x) {
  blah <- function(x) {
    s <- strsplit(tolower(x), " ")[[1]]
    paste(toupper(substring(s, 1,1)), substring(s, 2),
                   sep="", collapse=" ")
  }
  
  unname(sapply(x, FUN=blah))
}

# Bind the columns from a single row of full precinct information data frame 
# to the full precinct data
add.columns <- function(i, data.list, info.df) {
  df <- data.frame(data.list[i]) %>%
    cbind(info.df[i,])
  df
}


#-----------------
# 2005 precincts
#-----------------
path.to.raw <- "2005/Precinct list/raw_output/"

# Get list of files to parse
p.2005.data.files <- list.files(path.to.raw, pattern="_data")
p.2005.info.files <- list.files(path.to.raw, pattern="_info")

# Load the info files as a list of dataframes
p.2005.info.list <- lapply(paste0(path.to.raw, "/", p.2005.info.files), 
                           FUN=read_csv, col_names=FALSE,
                           col_types="cc")

# Combine the list and clean the final dataframe
p.2005.info <- bind_rows(p.2005.info.list) %>% 
  set_colnames(c("county", "district")) %>%
  mutate(county = title.case(gsub("COUNTY: ", "", county)),
         district = as.numeric(gsub("\\D+", "", district)))

# Load the data files as a list of dataframes
data.names <- c("code", "locality", "address", "polling.places",
                "voters", "non.ret.places", "non.ret.voters")
p.2005.data.list <- lapply(paste0(path.to.raw, "/", p.2005.data.files), 
                           FUN=read_csv, col_names=data.names, 
                           col_types=paste0(rep("c", 7), collapse=""))

# Simultaneously loop through the data and info lists and bind the 
# precinct information to each actual data dataframe
p.2005.raw <- bind_rows(lapply(1:nrow(p.2005.info), FUN=add.columns, 
                               data.list=p.2005.data.list, info=p.2005.info))

# Clean up final dataframe
p.2005 <- p.2005.raw %>%
  mutate(consolidated = ifelse(grepl("\\*", code), 1, 0),
         code = as.numeric(gsub("\\*", "", code))) %>%
  mutate(code = str_pad(code, width=5, pad="0")) %>%
  mutate(locality = title.case(locality),
         address = title.case(address)) %>%
  mutate(polling.places = as.numeric(gsub("\\D+", "", polling.places)),
         voters = as.numeric(gsub("\\D+", "", voters)),
         non.ret.places = as.numeric(gsub("\\D+", "", non.ret.places)),
         non.ret.voters = as.numeric(gsub("\\D+", "", non.ret.voters)))

# Write CSV file
write_csv(p.2005, path="2005/Precinct list/precincts_2005.csv")



#-----------------
# 2011 precincts
#-----------------
path.to.raw <- "2011/Precinct list/raw_output/"

# Get list of files to parse
p.2011.data.files <- list.files(path.to.raw, pattern="_data")
p.2011.info.files <- list.files(path.to.raw, pattern="_info")

# Load the info files as a list of dataframes
p.2011.info.list <- lapply(paste0(path.to.raw, "/", p.2011.info.files), 
                           FUN=read_csv, col_names=FALSE, col_types="cc")

# Combine the list and clean the final dataframe
p.2011.info <- bind_rows(p.2011.info.list) %>% 
  set_colnames(c("county", "district")) %>%
  mutate(county = title.case(gsub("COUNTY: ", "", county)),
         district = as.numeric(gsub("\\D+", "", district)))

# Load the data files as a list of dataframes
data.names <- c("code", "address", "locality", "polling.places", "voters")
p.2011.data.list <- lapply(paste0(path.to.raw, "/", p.2011.data.files), 
                           FUN=read_csv, col_names=data.names, 
                           col_types=paste0(rep("c", 5), collapse=""))

# Simultaneously loop through the data and info lists and bind the 
# precinct information to each actual data dataframe
p.2011.raw <- bind_rows(lapply(1:nrow(p.2011.info), FUN=add.columns, 
                               data.list=p.2011.data.list, info=p.2011.info))

# Clean up final dataframe
p.2011 <- p.2011.raw %>%
  mutate(code = str_pad(code, width=5, pad="0")) %>%
  mutate(locality = title.case(locality),
         address = title.case(address)) %>%
  mutate(polling.places = as.numeric(gsub("\\D+", "", polling.places)),
         voters = as.numeric(gsub("\\D+", "", voters)))

# Write CSV file
write_csv(p.2011, path="2011/Precinct list/precincts_2011.csv")


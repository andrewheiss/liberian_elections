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

# Remove columns where every value is NA (used with 2014)
shrink.columns <- function(df) {
  df.return <- Filter(function(x) !all(is.na(x)), data.frame(df))
  colnames(df.return) <- paste0("V", 1:ncol(df.return))
  df.return
}

# Search the whole dataframe for cells that contain county and district info
extract.info <- function(df) {
  df <- data.frame(df)  # Convert to actual dataframe
  
  matches <- apply(df, c(1, 2), function(x) grepl("COUNTY|ELECTORAL", x))
  extracted <- df[matches]
  return(data_frame(county = extracted[1], district = extracted[2]))
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
         non.ret.voters = as.numeric(gsub("\\D+", "", non.ret.voters))) %>%
  select(code, locality, address, voters, polling.places, county, district, 
         non.ret.places, non.ret.voters, consolidated)

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
         voters = as.numeric(gsub("\\D+", "", voters))) %>%
  select(code, locality, address, voters, polling.places, county, district)

# Write CSV file
write_csv(p.2011, path="2011/Precinct list/precincts_2011.csv")



#-----------------
# 2014 precincts
#-----------------
path.to.raw <- "2014/Precinct list/raw_output/"

# Get list of files to parse
p.2014.files <- list.files(path.to.raw)

# Load the files as a list of dataframes
# Need to use read.csv instead of read_csv because some CSV have
# different numbers of columns
p.2014.list <- lapply(paste0(path.to.raw, "/", p.2014.files), 
                      FUN=read.csv, stringsAsFactors=FALSE, skip=3, 
                      header=FALSE)

p.2014.info.list <- lapply(paste0(path.to.raw, "/", p.2014.files), 
                      FUN=read.csv, stringsAsFactors=FALSE, nrows=3, 
                      header=FALSE)

p.2014.info <- bind_rows(lapply(p.2014.info.list, FUN=extract.info)) %>% 
  mutate(county = title.case(gsub("COUNTY :", "", county)),
         district = as.numeric(gsub("\\D+", "", district)))


p.2014.list.shrunk <- lapply(p.2014.list, FUN=shrink.columns)

# Simultaneously loop through the data and info lists and bind the 
# precinct information to each actual data dataframe
p.2014.raw <- bind_rows(lapply(1:nrow(p.2014.info), FUN=add.columns,
                               data.list=p.2014.list.shrunk, info=p.2014.info)) 

p.2014 <- p.2014.raw %>%
  rename(code = V1, locality = V2, address = V3, voters = V4, polling.places = V5) %>%
  mutate(code = str_pad(code, width=5, pad="0")) %>%
  mutate(locality = title.case(locality),
         address = title.case(address)) %>%
  mutate(polling.places = as.numeric(gsub("\\D+", "", polling.places)),
         voters = as.numeric(gsub("\\D+", "", voters)))

# Write CSV file
write_csv(p.2014, path="2014/Precinct list/precincts_2014.csv")

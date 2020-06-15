#include <sstream>

#include <iostream>
#include <sstream>
#include <cstdlib>
#include <algorithm>
#include <cmath>
#include <vector>
#include <queue>
#include <stdexcept>

using namespace std;

typedef unsigned int uint;

/**
 * Solve reads data from the input stream and output data to the output stream.
 * 
 * Errors should be reported to cerr and/or thow an exception.
 * 
 * Solve can return some characteristics of the result.
 * 
 * Here we return number of strongly connected components.
 */ 
int solve( istream &in, ostream &out) {
  uint nvtx, nedg;
  in >> nvtx;
  in >> nedg;
  vector< vector<uint> > graph(nvtx);
  vector< vector<uint> > graph_t(nvtx);
  vector< uint> closing_seq(nvtx,0);
  vector< pair<uint, uint> > stack;
  
  uint vsrc, vdst;
  for(uint ie=0; ie<nedg; ie++) {
    in >>vsrc; in >> vdst;
    graph[vsrc].push_back(vdst);
  }
  
  // first pass + transpose
  uint out_time=0;
  for(uint iv=0; iv<nvtx; iv++) {
      if (! closing_seq[iv]) {
        closing_seq[iv]=1;
        stack.push_back( pair<uint,uint>(iv,-1) );
        while( stack.size() ) {
          if (++stack.back().second < graph[stack.back().first].size()) {
            uint ngh = graph[stack.back().first][stack.back().second];
            graph_t[ngh].push_back(stack.back().first);
          
            if (! closing_seq[ngh]) { // previsit
              closing_seq[ngh]=1;
              stack.push_back( pair<uint,uint>(ngh,-1));
            }
          } else { //postvisit
            closing_seq[stack.back().first]= (++out_time);
            graph[stack.back().first].clear();
            stack.pop_back();
          }  
        }
      }
  }  
  graph.clear();
  vector<uint> closing_order(nvtx);
  for(uint i=0; i<closing_seq.size();i++) 
    closing_order[ closing_seq[i]-1] = i, closing_seq[i]=0;
  
  uint comp=0;
  uint comp_size=0;
  vector<int> component_list;
  vector<uint> vtx_comp(nvtx);
  uint comp_min;
  for(int i=closing_order.size()-1; i>=0; i--) {
      uint iv=closing_order[i];
      if (! closing_seq[iv]) {
        comp++;  
        component_list.clear();
        comp_min=nvtx;
        //out << "component " << comp++ << endl;
        comp_size=0;
        closing_seq[iv]=1;
        stack.push_back( pair<uint,uint>(iv,-1) );
        while( stack.size() ) {
          if (++stack.back().second < graph_t[stack.back().first].size()) {
            uint ngh = graph_t[stack.back().first][stack.back().second];
          
            if (! closing_seq[ngh]) { // prvisit
              closing_seq[ngh]=1;
              stack.push_back(pair<uint,uint>(ngh,-1));
            }
          } else { // postvisit
            component_list.push_back( stack.back().first );
            if ( component_list.back() < comp_min) comp_min = component_list.back();  
            comp_size++;
            graph_t[stack.back().first].clear();
            stack.pop_back();
          }  
        }
        while(component_list.size() > 0) {
          vtx_comp[component_list.back()] = comp_min;
          component_list.pop_back();
        }  
        //cout << "component: " << comp << " " << comp_size << endl;
      }
  }
  for(uint i=0; i < nvtx;i++) 
    out << vtx_comp[i] << endl;
    
  out << "WRONG" << endl;
   return comp;
}



/**
 * make random oriented multigraph with loops
 * it is guaranteed, that number of componends is at least n_comp which is randomly generated
 * up to max_n_comp constant.
 * 
 * size - number of vertices
 * min_ngh, max_ngh - range of number of outcomming edges from single vertex 
 * n_comp - number of components
 */ 
void make_dataset(ostream &out_stream, uint size, uint min_ngh, uint max_ngh, uint n_comp) {
  
  vector<int> vtx_comp(size, -1); // components for vertices
  vector<vector<uint> > vtx_of_comp_t(n_comp); // vertexes of components (targeted)
  vector<vector<uint> > vtx_of_comp_u(n_comp); // vertexes of components (untargeted)

  if (n_comp > size) cerr << "n_comp: " << n_comp << " > n_vtx: " << size << endl;
  for(uint i=0; i< n_comp; i++) {
      uint idx = rand()%size;
      while(vtx_comp[idx]!=-1) {
          idx++;  // every component has at least one vtx          
          if (idx == size) idx=0;
      }    
      vtx_comp[idx] = i;
  }    
  for(uint i=0; i< size; i++) { // set remaining vtxes to components
    if (vtx_comp[i] == -1) vtx_comp[i]=rand()%n_comp;
    vtx_of_comp_u[ vtx_comp[i] ].push_back(i); // add to list of vertexes per component
    
    //cout << i << " " << vtx_comp[i] << endl;
  } 
  // shuffle component vtxes
  for(uint i=0; i<n_comp; i++) std::random_shuffle(vtx_of_comp_u[i].begin(), vtx_of_comp_u[i].end());
  
  // component meta DAG
  vector< vector<uint> > meta_edges(n_comp);
  for(uint i=0; i<n_comp-1; i++)  {
    uint n_out=rand()%(2*(n_comp-i-1));
    meta_edges[i].resize(n_out+1);
    meta_edges[i][0]=i;
    for(uint j=1; j<n_out+1; j++) meta_edges[i][j] = i+1+rand()%(n_comp -i-1);
  }
  meta_edges[n_comp-1].push_back(n_comp-1);
  
  vector< pair<uint, uint> > edges;
  // make whole graph
  for(uint comp=0; comp < n_comp; comp++) {
    // make simple cycle to make it strongly connected   
    for(uint i=0; i<vtx_of_comp_u[comp].size()-1; i++) 
      edges.push_back( pair<uint,uint> ( vtx_of_comp_u[comp][i], vtx_of_comp_u[comp][i+1]) );
    edges.push_back( pair<uint,uint> ( vtx_of_comp_u[comp].back(), vtx_of_comp_u[comp].front() ) );
    // add random edges 
    uint target_comp, target_vtx, source_vtx;
    for(uint i=0; i<vtx_of_comp_u[comp].size(); i++)  {
        uint n_ngh = min_ngh + rand() % (max_ngh - min_ngh) - 1;
        for(; n_ngh>0; n_ngh--) {
            if (rand()%10 == 1)  {
                // edges to connected  components
                target_comp = meta_edges[ comp ][ rand()%(meta_edges[ comp ].size()) ];          
            } else {
                // edges inside the component
                target_comp = comp;
            }
            source_vtx = vtx_of_comp_u[comp][i];
            target_vtx = vtx_of_comp_u[target_comp][ rand()%(vtx_of_comp_u[target_comp].size() ) ];
            // remove loop edges
            if (source_vtx != target_vtx)
                edges.push_back( pair<uint,uint>(source_vtx, target_vtx) );  
        }
    }    
  }              

  std::random_shuffle( edges.begin(), edges.end() );
  // Output
  out_stream << size << " " << edges.size() << endl;
  for(uint i=0;i<edges.size();i++) 
      out_stream << edges[i].first << " " << edges[i].second << endl;
}  
  
  
/**
 * Creates the test input data for the problem.
 * The problem size is given. The result data are output to the stream 'out'.
 * No checking should be performed. It is done by separate solve step.
 */  
void make_data(ostream &out, unsigned int problem_size) {
  uint n_vtx = problem_size;  
  uint ngh_min = 2;
  uint ngh_max = 5;
  uint n_comp=sqrt(problem_size);

  stringstream input_data;
  make_dataset(input_data, n_vtx, ngh_min, ngh_max, n_comp);  
 
  stringstream solve_output;
  int result_n_comp = solve(input_data, solve_output);  
  if (result_n_comp != n_comp) {
      cerr << "n comp differs, output: " << result_n_comp << " input: " << n_comp << endl;
  }
 
  out << input_data.str();  

}

int main(int argc, char* argv[]) {
    unsigned int problem_size = 0;
    uint random_seed=problem_size;
    
    for(int i =1; i<argc;i++) {       
        if (argv[i] == string("-p") ) {
            i++;
            if (i < argc) 
                stringstream(argv[i]) >> problem_size;
        } else if (argv[i] == string("-r")) {
            i++;
            if (i < argc) {
                istringstream ss(argv[i]);                    
                ss >> random_seed;
                if (ss.fail()) {
                    random_seed=problem_size; i--;
                }   
            }                           
        }
    }
    srand (random_seed);

    if (problem_size == 0) {
      solve( cin, cout);
    } else { 
      stringstream input_data;  
      make_data(input_data, problem_size );
      
      /*
      try {
        stringstream output_data;  
        solve(input_data, output_data);    
      } catch (...) {
        cerr << "Solve fails for generated data." << endl;
        throw;
      } */ 
      
      cout << input_data.str();
    }
    
    //
    //make_dataset("webisl_1000",1002, 4, 100);
    //make_dataset("webisl_10000",10374, 5,10);
    //make_dataset("webisl_1000000",987032, 2 , 20);
}  
